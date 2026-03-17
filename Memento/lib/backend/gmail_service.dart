import 'dart:async';
import 'dart:convert';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:googleapis/gmail/v1.dart' as gmail;
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

/// ─────────────────────────────────────────────────────────────
/// Simple HTTP client that injects OAuth headers
class _GoogleAuthClient extends http.BaseClient {
  final Map<String, String> _headers;
  final http.Client _inner = http.Client();
  _GoogleAuthClient(this._headers);
  @override
  Future<http.StreamedResponse> send(http.BaseRequest r) {
    r.headers.addAll(_headers);
    return _inner.send(r);
  }
}

/// ─────────────────────────────────────────────────────────────
/// Gmail integration (foreground + background-safe)
class GmailService {
  // NB: scopes must include readonly access
  static final GoogleSignIn _gs =
  GoogleSignIn(scopes: [gmail.GmailApi.gmailReadonlyScope]);

  static GoogleSignInAccount? _user;          // cached account
  static String? _lastFetchedId;              // newest Gmail ID we forwarded
  static Timer? _timer;                       // 10-min periodic timer

  /// Call once from UI to sign in & start the 10-min loop
  static Future<void> connectAndStart() async {
    // 1) interactive sign-in if needed
    _user = await _gs.signInSilently();
    _user ??= await _gs.signIn();
    if (_user == null) return; // user aborted

    // 2) persist _lastFetchedId (if any) – load it now
    final prefs = await SharedPreferences.getInstance();
    _lastFetchedId = prefs.getString('gmail_last_id');

    // 3) kick off the periodic fetcher (runs in both isolates)
    _startTimer();
  }

  /// Called from background-service isolate on every tick
  static Future<void> tryFetchLatestEmail() async {
    try {
      // silent sign-in is enough after first interactive auth
      _user ??= await _gs.signInSilently();
      if (_user == null) return;                         // cannot auth silently

      final api = gmail.GmailApi(_GoogleAuthClient(await _user!.authHeaders));

      // list newest msg id
      final items = await api.users.messages
          .list('me', maxResults: 1)
          .then((r) => r.messages ?? []);

      if (items.isEmpty) return;
      final id = items.first.id!;
      if (id == _lastFetchedId) return;                  // already forwarded

      // fetch full message (subject + plain-text body)
      final full = await api.users.messages.get('me', id, format: 'full');

      final subject = full.payload?.headers?.firstWhere(
            (h) => h.name == 'Subject',
        orElse: () => gmail.MessagePartHeader(
            name: 'Subject', value: '(no subject)'),
      ).value ??
          '(no subject)';

      final body = _extractBody(full) ?? '(no plain-text body)';

      // send to backend
      await _sendToBackend(subject, body);

      // remember id (persist so next app launch knows it)
      _lastFetchedId = id;
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('gmail_last_id', id);
    } catch (e) {
      // log but do not crash background isolate
      // (GoogleSignIn throws if silent auth fails)
      print('[GmailService] fetch error: $e');
    }
  }

  /* ───────────────────────── helpers ───────────────────────── */

  static void _startTimer() {
    _timer?.cancel();
    _timer = Timer.periodic(
      const Duration(minutes: 10),
          (_) => tryFetchLatestEmail(),
    );
  }

  static Future<void> _sendToBackend(String subject, String body) async {
    try {
      final ch = WebSocketChannel.connect(
        Uri.parse('ws://<YOUR_BACKEND_HOST>/agents/active'),
      );
      final payload = jsonEncode({
        'source': 'gmail',
        'subject': subject,
        'body': body,
        'time': DateTime.now().toIso8601String(),
      });
      ch.sink.add(payload);
      await Future.delayed(const Duration(seconds: 1));
      await ch.sink.close();
    } catch (e) {
      print('[GmailService] WebSocket error: $e');
    }
  }

  // recursively pull first text/plain part & decode
  static String? _extractBody(gmail.Message msg) {
    String? _decode(String? b64) =>
        b64 == null ? null : utf8.decode(base64Url.decode(b64));

    gmail.MessagePart? _walk(gmail.MessagePart p) {
      if (p.mimeType?.startsWith('text/plain') == true) return p;
      if (p.parts == null) return null;
      for (final cp in p.parts!) {
        final hit = _walk(cp);
        if (hit != null) return hit;
      }
      return null;
    }

    final part = _walk(msg.payload!) ?? msg.payload;
    return _decode(part?.body?.data);
  }
}

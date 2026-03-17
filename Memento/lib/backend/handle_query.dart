import 'dart:convert';
import 'dart:math';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:flutter/material.dart';
import 'package:flutter_tts/flutter_tts.dart';
import '/utils/notification_helper.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:real_volume/real_volume.dart';
// import 'package:flutter_timezone/flutter_timezone.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:web_socket_client/web_socket_client.dart';

class HandleQuery {
  static final stt.SpeechToText _speech = stt.SpeechToText();
  static final _tts = FlutterTts();
  static final StringBuffer _recognizedBuffer = StringBuffer();
  static String _lastFinalPhrase = "";
  static bool isRecordingActive = false;
  static bool replyTalking = false;
  static RingerMode? currentMode;
  static WebSocket? _socket;

  static Future<void> startListening(BuildContext context) async {
    replyTalking = true;
    final available = await _speech.initialize(
      onStatus: (status) {
        print('Speech status: $status');
      },
      onError: (error) {
        print('Speech error: $error');
      },
    );

    if (!available) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Speech recognition not available.')),
      );
      return;
    }

    _recognizedBuffer.clear();
    _lastFinalPhrase = "";
    isRecordingActive = true;

    await RealVolume.setRingerMode(RingerMode.SILENT, redirectIfNeeded: false);

    while (isRecordingActive) {
      await _speech.listen(
        listenFor: const Duration(minutes: 10),
        pauseFor: const Duration(minutes: 10),
        onResult: (result) {
          if (result.finalResult) {
            final newText = result.recognizedWords.trim();
            // print(newText);

            if (newText.isNotEmpty && newText != _lastFinalPhrase) {
              _recognizedBuffer.write(
                _recognizedBuffer.isEmpty ? newText : " $newText",
              );
              _lastFinalPhrase = newText;
            }
          }
        },
      );
    }
  }

  static Future<String> stopListening() async {
    isRecordingActive = false;
    await _speech.stop();
    await Future.delayed(const Duration(seconds: 3));
    await RealVolume.setRingerMode(RingerMode.NORMAL, redirectIfNeeded: false);

    final result = _recognizedBuffer.toString().trim();
    _recognizedBuffer.clear();
    _lastFinalPhrase = "";
    return result.isEmpty ? "No speech detected." : result;
  }

  static Future<void> _handleBackendResponse(
    BuildContext context,
    Map<String, dynamic> data,
    void Function(String, bool) onReply,
  ) async {
    final reply = data["reply"];
    final task = data["task"];

    final event = data["event"] ?? <String, dynamic>{};
    final reminder = data["reminder_message"] ?? "";

    final uuid = event?["id"] ?? "";
    final title = event?["title"] ?? "Reminder";

    if (reply.isNotEmpty) {
      print(reply);
      if (replyTalking) {
        await _tts.setLanguage("en-US");
        await _tts.setSpeechRate(0.5);
        await _tts.speak(reply);
      }
      onReply(reply, false);
      // if (context.mounted) {
      //   onReply(reply, false);
      // }
    }

    final int id = Random().nextInt(999) + 1;

    if (task == "delete") {
      if (event) await NotificationHelper.cancelNotification(id);
      return;
    }
    if (task == "query" || task == "conversation") {
      return;
    }
    if (event == null || reminder == null) return;

    final trigger = event["trigger"];
    if (trigger == "time") {
      final startTimeStr = event["start_time"];
      final endTimeStr = event["end_time"];
      final recurringSeconds = event["recurring"];
      if (recurringSeconds == null) {
        final startTime = DateTime.parse(startTimeStr);
        final notificationTime = startTime.subtract(const Duration(minutes: 5));
        final personalizedBody = reminder.replaceAll("#time#", "5 minutes");

        if (task == "schedule") {
          await NotificationHelper.scheduleNotification(
            id: id,
            title: title,
            body: personalizedBody,
            scheduledTime: notificationTime,
          );
        } else {
          await NotificationHelper.rescheduleNotification(
            id: id,
            title: title,
            body: personalizedBody,
            scheduledTime: notificationTime,
          );
        }
      } else {
        final baseTime = DateTime.parse(
          startTimeStr,
        ).subtract(const Duration(minutes: 5));
        final endTime = DateTime.parse(endTimeStr);
        final interval = Duration(seconds: recurringSeconds.round());
        var nextTime = baseTime;
        int recurrenceCount = 1;
        while (nextTime.isBefore(endTime)) {
          final recurringId = id + recurrenceCount;
          final personalizedBody = reminder.replaceAll("#time#", "5 minutes");
          if (task == "schedule") {
            await NotificationHelper.scheduleNotification(
              id: recurringId,
              title: title,
              body: personalizedBody,
              scheduledTime: nextTime,
            );
          } else {
            await NotificationHelper.rescheduleNotification(
              id: recurringId,
              title: title,
              body: personalizedBody,
              scheduledTime: nextTime,
            );
          }
          recurrenceCount++;
          nextTime = baseTime.add(interval * recurrenceCount);
        }
      }
    } else if (trigger == "location") {
      final prefs = await SharedPreferences.getInstance();
      final stored = prefs.getString("location_events");
      List<Map<String, dynamic>> locationEvents =
          stored != null
              ? List<Map<String, dynamic>>.from(jsonDecode(stored))
              : [];
      final locationEvent = {
        "id": id,
        "title": title,
        "place": event["place"],
        "reminder_message": reminder,
        "start_time": event["start_time"] ?? event["min_start_time"],
      };
      locationEvents.add(locationEvent);
      await prefs.setString("location_events", jsonEncode(locationEvents));
    }
  }

  static Future<void> sendQuery(
    BuildContext context,
    String queryText,
    void Function(String, bool) onReply,
  ) async {
    // print(queryText);

    final connectivityResult = await Connectivity().checkConnectivity();
    if (!connectivityResult.contains(ConnectivityResult.mobile) &&
        !connectivityResult.contains(ConnectivityResult.wifi)) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('No internet connection')));
      return;
    }

    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('token');
    if (token == null) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Authentication required')));
      return;
    }

    final uri = Uri.parse(
      'wss://memento-avdxhuanejbycxfm.italynorth-01.azurewebsites.net/agents/active',
    );

    try {
      _socket = WebSocket(
        uri,
        headers: {'Authorization': token, 'Content-Type': 'application/json'},
      );
    } catch (e) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Socket connection failed')));
      return;
    }

    // ── WAIT FOR HANDSHAKE TO COMPLETE ──
    await _socket!.connection.firstWhere((state) => state is Connected);

    // Send the initial payload
    final initialPayload = {
      "msg": queryText,
      "current_datetime": DateTime.now().toIso8601String(),
    };
    // print(initialPayload);
    _socket!.send(jsonEncode(initialPayload));
    print(initialPayload);

    // Listen for incoming messages
    _socket!.messages.listen(
      (message) async {
        try {
          print(message);
          final data = jsonDecode(message) as Map<String, dynamic>;
          await _handleBackendResponse(context, data, onReply);
        } catch (e) {
          print("Invalid JSON or processing error: $e");
        }
      },
      onError: (error) {
        print("WebSocket error: $error");
      },
      onDone: () {
        print("WebSocket connection closed by backend.");
      },
    );
  }
}

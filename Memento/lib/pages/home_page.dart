import 'dart:convert';
import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import '../backend/gmail_service.dart';
import '/widgets/custom_appbar.dart';
import '/backend/handle_query.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:flutter_background_service/flutter_background_service.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:flutter_timezone/flutter_timezone.dart';
import 'package:permission_handler/permission_handler.dart';

import 'package:connectivity_plus/connectivity_plus.dart';

import 'package:real_volume/real_volume.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '/utils/notification_helper.dart';
import 'package:geolocator/geolocator.dart';

import '../widgets/memento_drawer.dart';
import '../pages/query_page.dart';
import 'package:http/http.dart' as http;
import 'package:timezone/timezone.dart' as tz;
import 'package:timezone/data/latest.dart' as tz;
import 'package:web_socket_client/web_socket_client.dart';

class HomePage extends StatefulWidget {
  const HomePage({Key? key}) : super(key: key);

  @override
  State<HomePage> createState() => _HomePageState();
}

final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin =
    FlutterLocalNotificationsPlugin();

// --------------------------------------> "onstart" - The main function of the pipeline <------------------------------------------------------------
@pragma('vm:entry-point')
Future<void> onStart(ServiceInstance service) async {
  print('Service started');

  bool isRecording = false;
  final speech = stt.SpeechToText();
  final buffer = StringBuffer();
  RingerMode? currentMode;
  int sessionCounter = 0;
  String lastRecognized = "";
  bool finishSession = false;
  WebSocket? _socket;
  bool connectedSocket = false;

  String timeZoneRequest = await FlutterTimezone.getLocalTimezone();

  bool? isPermissionDNDGranted = await RealVolume.isPermissionGranted();
  if (!isPermissionDNDGranted!) {
    await RealVolume.openDoNotDisturbSettings();
  }

  bool available = await speech.initialize(
    onStatus: (status) async {
      print('Speech status: $status');

      if (status != "listening") {
        await RealVolume.setRingerMode(
          RingerMode.SILENT,
          redirectIfNeeded: false,
        );
      }
    },
    onError: (error) {
      print('Speech error: $error');
    },
  );
  if (!available) {
    print('Speech recognition not available.');
    return;
  }

  service.on('stopService').listen((_) {
    print('Stopping service.');
    service.stopSelf();
  });

  service.on('stopRecording').listen((event) async {
    isRecording = false;
    await speech.stop();
    await Future.delayed(const Duration(seconds: 1));
    await RealVolume.setRingerMode(
      currentMode == RingerMode.NORMAL ? RingerMode.NORMAL : RingerMode.SILENT,
      redirectIfNeeded: false,
    );

    final fullText = buffer.toString().trim();

    print(fullText);

    if (fullText.isNotEmpty) {
      final wordCount =
          fullText.split(RegExp(r'\s+')).where((w) => w.isNotEmpty).length;
      if (wordCount >= 10) {
        final prefs = await SharedPreferences.getInstance();
        final preEventsJson = prefs.getString('preEvents');

        List<Map<String, dynamic>> preEvents =
            preEventsJson != null
                ? List<Map<String, dynamic>>.from(jsonDecode(preEventsJson))
                : [];

        preEvents.add({
          "event": fullText,
          "time_zone": timeZoneRequest,
          "date": DateTime.now().toIso8601String(),
        });

        await prefs.setString('preEvents', jsonEncode(preEvents));
      }
    }
    buffer.clear();
    print("Recording stopped via command");
  });

  service.on('startRecording').listen((event) async {
    isRecording = true;
    sessionCounter = 0;
    currentMode = await RealVolume.getRingerMode();
  });

  Timer.periodic(const Duration(minutes: 10), (timer) async {
    print("Checking location and nearby places!");

    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        await Geolocator.openLocationSettings();
        return;
      }
      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.deniedForever ||
            permission == LocationPermission.denied) {
          return;
        }
      }

      Position position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );
      final lat = position.latitude;
      final lon = position.longitude;
      print("lat: $lat, lon: $lon");

      final query = """
[out:json];
(
  node(around:200,$lat,$lon)[amenity];
);
out body;
""";
      final url = Uri.parse("https://overpass-api.de/api/interpreter");
      final response = await http.post(url, body: {'data': query});

      if (response.statusCode != 200) {
        print("Failed to fetch places: ${response.statusCode}");
        return;
      }

      final data = jsonDecode(response.body);
      final List elements = data['elements'] as List;
      final places =
          elements.map<String>((e) {
            final name = e['tags']?['name'] ?? "Unnamed";
            final type = e['tags']?['amenity'] ?? "Unknown";
            final desc = e['tags']?['description'] ?? "";
            return "$type: $name${desc.isNotEmpty ? " — $desc" : ""}";
          }).toList();

      print(places);

      final bodyText =
          StringBuffer()
            ..writeln("lat: $lat, lon: $lon")
            ..writeln(places.join('\n'));
      tz.initializeTimeZones();
      tz.setLocalLocation(tz.getLocation('Africa/Cairo'));
      final scheduledDate = DateTime.now().add(const Duration(seconds: 10));

      await flutterLocalNotificationsPlugin.zonedSchedule(
        2000,
        'Location Reminder',
        bodyText.toString(),
        tz.TZDateTime.from(scheduledDate, tz.local),
        const NotificationDetails(
          android: AndroidNotificationDetails(
            'alarm_channel',
            'Alarm Notifications',
            importance: Importance.max,
            priority: Priority.high,
            autoCancel: true,
            icon: '@mipmap/ic_launcher',
          ),
        ),
        androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
      );

      final prefs = await SharedPreferences.getInstance();
      final stored = prefs.getString('location_events');
      if (stored == null) return;
      final List<dynamic> events = jsonDecode(stored);
      if (events.isEmpty) return;

      for (final event in events) {
        final eventPlace = event['place'] as String;
        final matches = elements.where(
          (e) => (e['tags']?['amenity'] ?? "") == eventPlace,
        );
        if (matches.isEmpty) continue;

        final id = event['id'] as int;
        final title = event['title'] as String;
        final scheduledTime = DateTime.parse(event['start_time'] as String);
        final template = event['reminder_message'] as String;

        for (final match in matches) {
          final placeName = match['tags']?['name'] ?? "Unnamed";
          final body = template.replaceAll('#place#', placeName);

          await NotificationHelper.scheduleNotification(
            id: id,
            title: title,
            body: body,
            scheduledTime: scheduledTime,
          );
        }
      }
    } catch (e) {
      print("Error in location timer: $e");
    }
  });

  Future<void> _handleSocketResponse(Map<String, dynamic> data) async {
    bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
    // TODO --> Continue after Testing
    if (!serviceEnabled) {
      // await Geolocator.openLocationSettings();
    } else {}
  }

  // Gmail poller ─ every 10 minutes
  Timer.periodic(const Duration(minutes: 10), (_) async {
    await GmailService.tryFetchLatestEmail();
  });


  Future<void> _handleBackendResponse(
    Map<String, dynamic> data,
  ) async {
    final task = data["task"];
    final event = data["event"] ?? <String, dynamic>{};
    final reminder = data["reminder_message"] ?? "";
    final id = event?["id"] ?? "";
    final title = event?["title"] ?? "Reminder";

    // final int id = Random().nextInt(999) + 1;

    if (task == "delete") {
      if (event) await NotificationHelper.cancelNotification(id);
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
        final personalizedBody = reminder.replaceAll("#time#", "5 minutes");
        final notificationTime = startTime.subtract(const Duration(minutes: 5));

        if (task == "schedule") {
          await NotificationHelper.scheduleNotification(
            id: id,
            title: title,
            body: personalizedBody,
            scheduledTime: notificationTime,
          );
        } else if (task == "update") {
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
          final personalizedBody = reminder.replaceAll(
            "#time#",
            "5 minutes",
          );

          if (task == "schedule") {
            await NotificationHelper.scheduleNotification(
              id: recurringId,
              title: title,
              body: personalizedBody,
              scheduledTime: nextTime,
            );
          } else if (task == "update") {
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

  Timer.periodic(const Duration(minutes: 2), (timer) async {
    if (isRecording) {
      finishSession = true;
    }

    final connectivityResult = await Connectivity().checkConnectivity();
    if (connectivityResult.contains(ConnectivityResult.mobile) ||
        connectivityResult.contains(ConnectivityResult.wifi)) {
      print("Connectivity available — checking preEvents...");

      final prefs = await SharedPreferences.getInstance();
      final preEventsJson = prefs.getString('preEvents');

      if (preEventsJson != null) {
        List<Map<String, dynamic>> preEvents = List<Map<String, dynamic>>.from(
          jsonDecode(preEventsJson),
        );

        if (preEvents.isNotEmpty) {
          if (false || !connectedSocket) {
            final prefs = await SharedPreferences.getInstance();
            final token = prefs.getString('token');
            final uri = Uri.parse(
              'wss://memento-avdxhuanejbycxfm.italynorth-01.azurewebsites.net/agents/passive',
            );
            try {
              _socket = WebSocket(
                uri,
                headers: {
                  'Authorization': token,
                  'Content-Type': 'application/json',
                },
              );
            } catch (e) {
              print("Socket Connection Failed");
              return;
            }
            await _socket!.connection.firstWhere((state) => state is Connected);
            connectedSocket = true;
            _socket!.messages.listen(
              (message) async {
                try {
                  print(message);
                  final data = jsonDecode(message) as Map<String, dynamic>;
                  await _handleSocketResponse(data);
                } catch (e) {
                  print("Invalid JSON or processing error: $e");
                }
              },
              onError: (error) {
                connectedSocket = false;
                print("WebSocket error: $error");
              },
              onDone: () {
                connectedSocket = false;
                print("WebSocket connection closed by backend.");
              },
            );
          }
          if (connectedSocket) {
            final initialPayload = {
              "msg": preEvents[0]["event"],
              "current_datetime": DateTime.now().toIso8601String(),
            };
            _socket!.send(jsonEncode(initialPayload));
          }
          print("All preEvents sent and cleared.");
        } else {
          print("No preEvents to send.");
        }
      }
    } else {
      print("No connectivity. Will retry later.");
    }
  });

  while (true) {
    if (!isRecording) {
      await Future.delayed(const Duration(seconds: 3));
      continue;
    }

    if (speech.isNotListening) {
      await RealVolume.setRingerMode(
        RingerMode.SILENT,
        redirectIfNeeded: false,
      );
      // await Future.delayed(const Duration(milliseconds: 500));
      await speech.listen(
        listenFor: const Duration(minutes: 5),
        pauseFor: const Duration(minutes: 5),
        onResult: (result) {
          if (result.finalResult) {
            final newText = result.recognizedWords.trim();

            if (newText != lastRecognized && newText.isNotEmpty) {
              buffer.write("$newText ");
              lastRecognized = newText;
            }
          }
        },
      );
      await Future.delayed(const Duration(milliseconds: 1200));
    } else {
      // await Future.delayed(const Duration(milliseconds: 500));
      await RealVolume.setRingerMode(
        currentMode == RingerMode.NORMAL
            ? RingerMode.NORMAL
            : RingerMode.SILENT,
        redirectIfNeeded: false,
      );
    }

    // await Future.delayed(const Duration(seconds: 1));

    if (finishSession) {
      sessionCounter++;
      finishSession = false;

      final fullText = buffer.toString().trim();
      if (fullText.isNotEmpty) {
        final wordCount =
            fullText.split(RegExp(r'\s+')).where((w) => w.isNotEmpty).length;
        if (wordCount < 10) {
          if (sessionCounter >= 5) {
            // No Activity -> stop automatically
            await flutterLocalNotificationsPlugin.cancel(1001);
            isRecording = false;
            await speech.stop();
            await Future.delayed(const Duration(seconds: 1));
            await RealVolume.setRingerMode(
              currentMode == RingerMode.NORMAL
                  ? RingerMode.NORMAL
                  : RingerMode.SILENT,
              redirectIfNeeded: false,
            );

            buffer.clear();
          }
          continue;
        } else {
          sessionCounter = 0;
          buffer.clear();
          print("Collected text: $fullText");

          final prefs = await SharedPreferences.getInstance();
          final preEventsJson = prefs.getString('preEvents');
          List<Map<String, dynamic>> preEvents =
              preEventsJson != null
                  ? List<Map<String, dynamic>>.from(jsonDecode(preEventsJson))
                  : [];

          preEvents.add({
            "event": fullText,
            "time_zone": timeZoneRequest,
            "date": DateTime.now().toIso8601String(),
          });
          await prefs.setString('preEvents', jsonEncode(preEvents));

          print('Saved offline query to preEvents.');
        }
      } else {
        if (sessionCounter >= 5) {
          // ! Problem with the "isRecording" state in the UI
          // final prefs = await SharedPreferences.getInstance();
          // await prefs.setBool('isRecording', false);

          await flutterLocalNotificationsPlugin.cancel(1001);
          await speech.stop();
          await RealVolume.setRingerMode(
            currentMode == RingerMode.NORMAL
                ? RingerMode.NORMAL
                : RingerMode.SILENT,
            redirectIfNeeded: false,
          );

          buffer.clear();
          isRecording = false;
        }
        continue;
      }
    } else {
      continue;
    }
  }
}

class _HomePageState extends State<HomePage>
    with SingleTickerProviderStateMixin {
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();
  final TextEditingController _queryController = TextEditingController();
  final GlobalKey<QueryPageState> _queryPageKey = GlobalKey<QueryPageState>();

  late final FlutterBackgroundService service;

  bool isRecording = false;
  bool isListeningQuery = false;
  bool showStopQueryButton = false;
  String _queryText = '';

  @override
  void initState() {
    super.initState();
    _initRecordingState();
    _initializeBackgroundService();

    _queryController.addListener(() {
      setState(() {
        _queryText = _queryController.text.trim();
      });
    });

    // Timer.periodic(Duration(seconds: 10), (_) async {
    //   final prefs = await SharedPreferences.getInstance();
    //   final recordingState = prefs.getBool('isRecording') ?? false;
    //   if (isRecording) {
    //     setState(() {
    //       isRecording = recordingState;
    //     });
    //   }
    // });
  }

  Future<void> _initRecordingState() async {
    final prefs = await SharedPreferences.getInstance();
    final isRecordingState = prefs.getBool('isRecording') ?? false;

    setState(() {
      isRecording = isRecordingState;
    });
  }

  Future<void> _initializeBackgroundService() async {
    await _requestPermissions();

    final service = FlutterBackgroundService();
    final isRunning = await service.isRunning();
    if (!isRunning) {
      await service.configure(
        iosConfiguration: IosConfiguration(
          autoStart: false,
          onForeground: onStart,
        ),
        androidConfiguration: AndroidConfiguration(
          autoStart: true,
          onStart: onStart,
          isForegroundMode: false,
          autoStartOnBoot: true,
          // notificationChannelId: 'my_foreground',
          // initialNotificationTitle: 'Memento is running',
          // initialNotificationContent: 'Listening in the background...',
          // foregroundServiceNotificationId: 888,
        ),
      );

      await service.startService();
      print("Background service started.");
    } else {
      print("Background service already running.");
    }
  }

  @override
  void dispose() {
    _queryController.dispose();
    super.dispose();
  }

  Future<void> _requestPermissions() async {
    // Mic
    final status = await Permission.microphone.status;
    if (!status.isGranted) {
      final result = await Permission.microphone.request();
      if (result.isGranted) {
        print('Microphone permission granted');
      } else {
        print('Microphone permission not granted');
      }
    }

    // Don't Disturb
    bool? isPermissionDNDGranted = await RealVolume.isPermissionGranted();
    if (!isPermissionDNDGranted!) {
      await RealVolume.openDoNotDisturbSettings();
    }

    // Location
    LocationPermission permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.deniedForever ||
          permission == LocationPermission.denied) {
        return;
      }
    }
  }

  Future<void> _handleStartRecording({String mode = 'passive'}) async {
    if (mode == 'active') {
      final prefs = await SharedPreferences.getInstance();
      final isRecording = prefs.getBool('isRecording') ?? false;

      if (!isRecording) {
        return;
      }
    }

    final service = FlutterBackgroundService();
    final isRunning = await service.isRunning();
    if (!isRunning) {
      await _initializeBackgroundService();
    }
    service.invoke('startRecording');

    const AndroidNotificationDetails androidPlatformChannelSpecifics =
        AndroidNotificationDetails(
          'recording_channel',
          'Recording Service',
          importance: Importance.max,
          priority: Priority.high,
          ongoing: true,
          autoCancel: false,
          onlyAlertOnce: true,
          icon: '@mipmap/ic_launcher',
        );

    const NotificationDetails platformChannelSpecifics = NotificationDetails(
      android: androidPlatformChannelSpecifics,
    );

    await flutterLocalNotificationsPlugin.show(
      1001, // Custom ID
      'Background Recording',
      'Recording is running...',
      platformChannelSpecifics,
      payload: 'from_notification',
    );

    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('isRecording', true);

    setState(() {
      isRecording = true;
    });
  }

  Future<void> _stopRecording({String mode = 'passive'}) async {
    final service = FlutterBackgroundService();
    service.invoke('stopRecording');

    await flutterLocalNotificationsPlugin.cancel(1001);

    if (mode == 'passive') {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool('isRecording', false);
    }

    setState(() {
      isRecording = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      resizeToAvoidBottomInset: true,
      key: _scaffoldKey,
      appBar: CustomAppBar(
        title: 'Memento',
        scaffoldKey: _scaffoldKey,
        showKnob: true,
        isRecording: isRecording,
        onStartRecording: () async {
          await _handleStartRecording();
        },
        onStopRecording: () async {
          await _stopRecording();
        },
      ),
      drawer: const MementoDrawer(),
      body: QueryPage(
        key: _queryPageKey,
        queryController: _queryController,
        isListeningQuery: isListeningQuery,
        showStopQueryButton: showStopQueryButton,
        showSendButton: _queryText.isNotEmpty,
        onStartListening: () async {
          await _stopRecording(mode: 'active');
          await Future.delayed(const Duration(seconds: 2));
          setState(() {
            isListeningQuery = true;
            showStopQueryButton = true;
          });
          await HandleQuery.startListening(context);
        },
        onStopListening: () async {
          final queryText = await HandleQuery.stopListening();
          await _handleStartRecording(mode: 'active');
          setState(() {
            isListeningQuery = false;
            showStopQueryButton = false;
            _queryText = queryText.trim();
          });
        },
        onSendQuery: () async {
          if (_queryText.isNotEmpty) {
            _queryPageKey.currentState?.addReply(
              _queryText,
              isUser: true,
            ); // show user message immediately
            _queryPageKey.currentState?.setLoading(true);

            await HandleQuery.sendQuery(context, _queryText, (
              replyText,
              isuser,
            ) {
              if (mounted) {
                _queryPageKey.currentState?.addReply(
                  replyText,
                  isUser: isuser,
                ); // Memento reply
              }
            });

            _queryController.clear();
            setState(() {
              _queryText = '';
            });
          }
        },
      ),
    );
  }
}

import 'dart:async';
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'pages/login_page.dart';
import 'pages/signup_page.dart';
import 'pages/onboarding_page.dart';
import 'pages/home_page.dart';
import 'pages/profile_page.dart';
import 'pages/subscriptions_page.dart';
import 'pages/settings_page.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:timezone/data/latest_all.dart' as tz;
import 'package:timezone/timezone.dart' as tz;
import 'package:flutter_timezone/flutter_timezone.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp();

  // Temp code if the app closed unnaturally or some problem occured 
  // final prefs = await SharedPreferences.getInstance();
  // await prefs.setBool('isRecording', false);

  final navigatorKey = GlobalKey<NavigatorState>();

  final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin =
    FlutterLocalNotificationsPlugin();
  final StreamController<NotificationResponse> streamController =
      StreamController();

  //  <------------------- Just for initialization -------------------->
  tz.initializeTimeZones();
  final String currentTimeZone = await FlutterTimezone.getLocalTimezone();
  tz.setLocalLocation(tz.getLocation(currentTimeZone));

  const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
  const initSettings = InitializationSettings(android: androidSettings);

  final navKey = GlobalKey<NavigatorState>();

  await flutterLocalNotificationsPlugin.initialize(
    initSettings,
    onDidReceiveNotificationResponse: (NotificationResponse response) async {
      streamController.add(response);

      final prefs = await SharedPreferences.getInstance();
      final talk = prefs.getBool('app_talk_reminder') ?? true;

      // >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> "Stop Service" Button in the persistent notification >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
      // if (response.actionId == 'STOP_SERVICE') {
      //   final service = FlutterBackgroundService();
      //   service.invoke('stopService');
      //   await flutterLocalNotificationsPlugin.cancel(1001);
      //   final prefs = await SharedPreferences.getInstance();
      //   await prefs.setBool('isRecording', false);
      // }
      // >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

      if (response.payload == 'from_notification') {
        navKey.currentState?.pushNamedAndRemoveUntil(
          '/home',
          (route) => false,
        ); 
      }

      if (talk && response.payload != null && response.payload != "from_notification") {
        final tts = FlutterTts();
        await tts.setLanguage("en-US");
        await tts.setSpeechRate(0.5);
        await tts.speak(response.payload!);
      }
    },
  );

  runApp(MyApp(navigatorKey: navigatorKey));
}


class MyApp extends StatefulWidget {
  final GlobalKey<NavigatorState> navigatorKey;
  const MyApp({super.key, required this.navigatorKey});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  // String _initialRoute = '/home'; 
  bool _loading = true;
  String? _initialRoute;

  @override
  void initState() {
    super.initState();
    determineInitialRoute();
  }

  Future<void> determineInitialRoute() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    String? token = prefs.getString('token');
    String? tokenIssueDateStr = prefs.getString('token_issue_date');
    bool? tokenValidity = prefs.getBool('token_validity');

    if (token == null || tokenIssueDateStr == null) {
      setState(() {
        // _initialRoute = '/home';
        _initialRoute = '/onboarding';
        _loading = false;
      });
      return;
    }

    try {
      final tokenIssueDate = DateTime.parse(tokenIssueDateStr);
      final now = DateTime.now();

      final difference = now.difference(tokenIssueDate);
      if (difference.inDays > 90 || !tokenValidity!) {
        setState(() {
          _initialRoute = '/login';
          _loading = false;
        });
        return;
      }

      setState(() {
        // _initialRoute = '/signup';
        _initialRoute = '/home';
        // _initialRoute = '/onboarding';
        _loading = false;
      });
    } catch (e) {
      print('Error parsing token issue date: $e');
      setState(() {
        _initialRoute = '/onboarding';
        _loading = false;
      });
    }
  }


  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    return MaterialApp(
      navigatorKey: widget.navigatorKey,

      debugShowCheckedModeBanner: false,
      title: 'Memento',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        scaffoldBackgroundColor: Colors.white,
      ),
      initialRoute: _initialRoute,
      routes: {
        '/onboarding': (context) => const OnboardingPage(),
        '/login': (context) => const LoginPage(),
        '/signup': (context) => const SignupPage(),
        '/home': (context) => const HomePage(),
        '/profile': (context) => const ProfilePage(),
        '/subscriptions': (context) => SubscriptionsPage(),
        '/settings': (context) => const SettingsPage()
      },
    );
  }
}

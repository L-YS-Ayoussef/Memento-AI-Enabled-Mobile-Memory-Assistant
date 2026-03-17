import 'package:flutter/material.dart';

class OnboardingPage extends StatefulWidget {
  const OnboardingPage({Key? key}) : super(key: key);

  @override
  State<OnboardingPage> createState() => _OnboardingPageState();
}

class _OnboardingPageState extends State<OnboardingPage> {
  bool _isChecked = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: 24.0,
              vertical: 16.0,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 40),
                // Logo Image
                Center(
                  child: Image.asset(
                    'assets/images/memento_logo.png',
                    height: 150,
                  ),
                ),
                const SizedBox(height: 40),
                // Welcome Title
                const Center(
                  child: Text(
                    "Welcome to Memento!",
                    style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
                    textAlign: TextAlign.center,
                  ),
                ),
                const SizedBox(height: 20),
                const Text(
                  "Memento is your personal memory assistant.\n\n"
                  "It helps you by recording your day, forming important events, "
                  "and reminding you about them automatically.\n\n"
                  "Whenever you need to remember what happened today, just ask Memento!",
                  style: TextStyle(fontSize: 16, height: 1.5),
                  textAlign: TextAlign.left,
                ),
                const SizedBox(height: 30),
                const Center(
                  child: Text(
                    "How to use Memento?",
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600),
                    textAlign: TextAlign.center,
                  ),
                ),
                const SizedBox(height: 15),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: const [
                    BulletPoint(
                      text: "Simply start the assistant from the Home page.",
                    ),
                    BulletPoint(
                      text:
                          "Memento will automatically listen in the background.",
                    ),
                    BulletPoint(
                      text:
                          "You will be reminded at the right time or location.",
                    ),
                    BulletPoint(
                      text:
                          "You can ask Memento questions anytime about your day.",
                    ),
                    SizedBox(height: 12),
                    Text(
                      "You don't need to do anything else. It's that simple!",
                      style: TextStyle(fontSize: 16, height: 1.5),
                    ),
                  ],
                ),
                const SizedBox(height: 30),
                Row(
                  children: [
                    Checkbox(
                      value: _isChecked,
                      onChanged: (bool? value) {
                        setState(() {
                          _isChecked = value ?? false;
                        });
                      },
                    ),
                    const Expanded(
                      child: Text(
                        "I agree to the Terms and Conditions",
                        style: TextStyle(fontSize: 14),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    onPressed:
                        _isChecked
                            ? () {
                              Navigator.pushNamed(context, '/signup');
                            }
                            : null,
                    child: const Text("Next", style: TextStyle(fontSize: 18)),
                    style: ElevatedButton.styleFrom(
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                      backgroundColor: const Color(
                        0xFF00B3FF,
                      ), 
                      disabledBackgroundColor:
                          Colors.grey, 
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class BulletPoint extends StatelessWidget {
  final String text;

  const BulletPoint({super.key, required this.text});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            "•",
            style: TextStyle(
              fontSize: 22, // Larger bullet
              height: 1.4,
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(fontSize: 16, height: 1.5),
            ),
          ),
        ],
      ),
    );
  }
}

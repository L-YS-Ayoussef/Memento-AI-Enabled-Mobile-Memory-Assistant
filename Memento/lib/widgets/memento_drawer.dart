import 'package:flutter/material.dart';
import 'package:animated_text_kit/animated_text_kit.dart';

class MementoDrawer extends StatelessWidget {
  const MementoDrawer({super.key});

  @override
  Widget build(BuildContext context) {
    return Drawer(
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          Container(
            color: const Color.fromARGB(255, 174, 204, 238),
            padding: const EdgeInsets.symmetric(vertical: 24),
            child: Column(
              children: [
                ClipOval(
                  child: Image.asset(
                    'assets/images/memento_logo.png',
                    height: 100,
                    width: 100,
                    fit: BoxFit.cover,
                  ),
                ),
                const SizedBox(height: 12),
                SizedBox(
                  height: 24,
                  child: AnimatedTextKit(
                    repeatForever: true,
                    animatedTexts: [
                      TypewriterAnimatedText(
                        'Life Remembers Itself!',
                        textStyle: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w500,
                        ),
                        speed: const Duration(milliseconds: 100),
                      ),
                    ],
                    isRepeatingAnimation: true,
                    pause: const Duration(milliseconds: 1000),
                    displayFullTextOnTap: false,
                  ),
                ),
              ],
            ),
          ),
          // const Divider(),
          ListTile(
            leading: const Icon(Icons.home_outlined),
            title: const Text('Home'),
            onTap: () => Navigator.pushNamed(context, '/home'),
          ),
          ListTile(
            leading: const Icon(Icons.person_outline),
            title: const Text('Profile'),
            onTap: () => Navigator.pushNamed(context, '/profile'),
          ),
          ListTile(
            leading: const Icon(Icons.subscriptions_outlined),
            title: const Text('Subscriptions'),
            onTap: () => Navigator.pushNamed(context, '/subscriptions'),
          ),
          ListTile(
            leading: const Icon(Icons.settings_outlined),
            title: const Text('Settings'),
            onTap: () => Navigator.pushNamed(context, '/settings'),
          ),
        ],
      ),
    );
  }
}

import 'package:flutter/material.dart';

class MementoKnob extends StatelessWidget {
  final VoidCallback onToggle;
  final bool isOn;

  const MementoKnob({super.key, required this.onToggle, required this.isOn});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onToggle,
      child: Container(
        width: 36,
        height: 36,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: isOn ? Colors.green : Colors.grey.shade300,
        ),
        child: Icon(
          isOn ? Icons.power_settings_new : Icons.circle_outlined,
          color: isOn ? Colors.white : Colors.black54,
          size: 20,
        ),
      ),
    );
  }
}

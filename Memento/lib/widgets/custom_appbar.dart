import 'package:flutter/material.dart';
import 'memento_knob.dart';

class CustomAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final GlobalKey<ScaffoldState> scaffoldKey;
  final VoidCallback? onStartRecording;
  final VoidCallback? onStopRecording;
  final bool showKnob;
  final bool isRecording;

  const CustomAppBar({
  super.key,
  required this.title,
  required this.scaffoldKey,
  this.showKnob = false,
  this.onStartRecording,
  this.onStopRecording,
  this.isRecording = false,
});



  @override
  Widget build(BuildContext context) {
    return AppBar(
      backgroundColor: const Color(0xFF00B3FF),
      title: Text(title),
      leading: IconButton(
        icon: const Icon(Icons.menu),
        onPressed: () => scaffoldKey.currentState?.openDrawer(),
      ),
      actions:
          showKnob
              ? [
                Padding(
                  padding: const EdgeInsets.only(right: 16),
                  child: MementoKnob(
                    onToggle: () {
                      final nextState = !isRecording;

                      if (nextState) {
                        onStartRecording?.call();
                      } else {
                        onStopRecording?.call();
                      }
                    },
                    isOn: isRecording, 
                  ),
                ),
              ]
              : null,
    );
  }

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight);
}

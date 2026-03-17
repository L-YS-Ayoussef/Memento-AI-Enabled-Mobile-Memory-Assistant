import 'package:flutter/material.dart';
import '/backend/gmail_service.dart';
import '/backend/settings_service.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({Key? key}) : super(key: key);

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  bool enableVibration = true;
  int timeoutSeconds = 10;
  bool appTalkReminder = true;
  bool darkMode = false;

  bool hasChanges = false;

  @override
  void initState() {
    super.initState();
    loadSettings();
  }

  Future<void> loadSettings() async {
    final settings = await SettingsService.loadSettings();
    setState(() {
      enableVibration = settings['enable_vibration'];
      timeoutSeconds = settings['timeout_seconds'];
      appTalkReminder = settings['app_talk_reminder'];
      darkMode = settings['dark_mode'];
    });
  }

  void markChanged() {
    setState(() {
      hasChanges = true;
    });
  }

  Future<void> saveSettings() async {
    await SettingsService.saveSettings(
      enableVibration: enableVibration,
      timeoutSeconds: timeoutSeconds,
      appTalkReminder: appTalkReminder
    );
    setState(() {
      hasChanges = false;
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Settings saved successfully!'),
        backgroundColor: Colors.green,
      ),
    );
  }

  Widget _buildSwitchTile(String title, bool value, Function(bool) onChanged) {
    return SwitchListTile(
      title: Text(title),
      value: value,
      onChanged: (val) {
        onChanged(val);
        markChanged();
      },
    );
  }

  Widget _buildNumberInputTile(
    String title,
    int value,
    Function(int) onChanged,
  ) {
    return ListTile(
      title: Text(title),
      trailing: SizedBox(
        width: 80,
        child: TextFormField(
          initialValue: value.toString(),
          keyboardType: TextInputType.number,
          onChanged: (val) {
            int parsed = int.tryParse(val) ?? value;
            onChanged(parsed);
            markChanged();
          },
          decoration: const InputDecoration(border: OutlineInputBorder()),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            _buildSwitchTile(
              'Enable Vibration',
              enableVibration,
              (val) => enableVibration = val,
            ),
            const SizedBox(height: 10),
            _buildNumberInputTile(
              'Notification Timeout (seconds)',
              timeoutSeconds,
              (val) => timeoutSeconds = val,
            ),
            const SizedBox(height: 10),
            _buildSwitchTile(
              'App Talks to Remind',
              appTalkReminder,
              (val) => appTalkReminder = val,
            ),
            const SizedBox(height: 20),
            _buildSwitchTile(
              'Dark Mode',
              darkMode,
              (val) => darkMode = val,
            ),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              icon: const Icon(Icons.email_outlined),
              label: const Text('Connect Gmail & Start Fetching'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.redAccent,        // pick any accent color
                padding: const EdgeInsets.symmetric(vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              onPressed: () async {
                await GmailService.connectAndStart();
                if (!context.mounted) return;
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Gmail connected – will check every 10 min')),
                );
              },
            ),
            const SizedBox(height: 20),

            if (hasChanges)
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: saveSettings,
                  icon: const Icon(Icons.save_outlined),
                  label: const Text('Save Changes'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

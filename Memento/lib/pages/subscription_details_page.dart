import 'package:flutter/material.dart';

class SubscriptionDetailsPage extends StatelessWidget {
  final Map<String, dynamic> subscription;

  const SubscriptionDetailsPage({Key? key, required this.subscription})
    : super(key: key);

  List<String> _getFeatures(String planName) {
    switch (planName.toLowerCase()) {
      case 'basic':
        return [
          'Passive mode with speech recognition every 30 seconds',
          'Uses on-device model for offline transcription',
          'Local notifications for time-based events',
          'Manual start/stop of passive mode',
          'Settings customization (vibration, read aloud, etc.)',
          'Dashboard access for past 24 hours',
          'No data sync between devices',
        ];
      case 'plus':
        return [
          'All Basic features included',
          'Location-based reminders and GPS event detection',
          'Weekly activity summaries (visited places, completed tasks)',
          'Extended dashboard with 30-day history',
          'Voice-based diary entries and daily logs',
          'Smart no-activity detection with notifications',
          'Priority access to new speech models and updates',
        ];
      case 'premium':
        return [
          'All Plus features included',
          'Integration with Gmail for parsing meetings and tasks',
          'Real-time reminders from emails and calendar',
          'Smart suggestions (breaks, deadlines, personalized routines)',
          'Unlimited passive mode uptime',
          'Cross-device sync and encrypted cloud backup',
          'Custom wake word support (planned feature)',
          'Priority support and beta access',
        ];
      default:
        return [];
    }
  }

  @override
  Widget build(BuildContext context) {
    final planName = subscription['plan_name'];
    final features = _getFeatures(planName);
    final image = subscription['image'];
    final shortDescription = subscription['short_description'];
    final price = subscription['price'];

    return Scaffold(
      appBar: AppBar(title: Text('${subscription['plan_name']} Subscription')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: Image.asset(
                  image,
                  height: 160,
                  width: 160,
                  fit: BoxFit.cover,
                ),
              ),
            ),
            const SizedBox(height: 24),
            Text(
              planName,
              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            Text(shortDescription, style: const TextStyle(fontSize: 16)),
            const SizedBox(height: 16),
            Text(
              'Price: $price',
              style: const TextStyle(
                fontSize: 18,
                color: Colors.blue,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 24),
            const Text(
              'What\'s included:',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 12),
            ...features.map(
              (feature) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('• ', style: TextStyle(fontSize: 16)),
                    Expanded(
                      child: Text(
                        feature,
                        style: const TextStyle(fontSize: 16),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text("Subscription flow not implemented."),
                    ),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.blue,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: const Text(
                  'Subscribe Now',
                  style: TextStyle(fontSize: 18),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

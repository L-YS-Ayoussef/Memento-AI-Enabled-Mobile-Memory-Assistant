import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ProfilePage extends StatefulWidget {
  const ProfilePage({Key? key}) : super(key: key);

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  final Map<String, dynamic> userData = {
    'full_name': 'Youssef Alaa',
    'email': 'youssef@gmail.com',
    'age': 21,
    'gender': "male",
    'subscription': 'Basic',
  };

  final List<Map<String, String>> dummyActivities = [
    {'description': 'Went for a walk in the park', 'time': '09:00 AM'},
    {'description': 'Attended team meeting', 'time': '11:00 AM'},
    {'description': 'Completed grocery shopping', 'time': '03:00 PM'},
  ];

  late List<DateTime> recentDays;
  late DateTime selectedDay;

  @override
  void initState() {
    super.initState();
    recentDays =
        List.generate(
          8,
          (index) => DateTime.now().subtract(Duration(days: index)),
        ).reversed.toList();
    selectedDay = recentDays.last;
  }

  Widget _buildInfoCard(String title, String value) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      elevation: 3,
      child: ListTile(
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text(value, style: const TextStyle(color: Colors.black87)),
      ),
    );
  }

  Widget _buildActivityCard(Map<String, String> activity) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 6, horizontal: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      elevation: 2,
      child: ListTile(
        title: Text(activity['description'] ?? ''),
        subtitle: Text('Time: ${activity['time'] ?? ''}'),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Logout',
            onPressed: () async {
              final prefs = await SharedPreferences.getInstance();
              await prefs.setBool('token_validity', false);
              if (!context.mounted) return;
              Navigator.pushReplacementNamed(context, '/login');
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            const SizedBox(height: 20),
            const CircleAvatar(
              radius: 50,
              backgroundImage: AssetImage('assets/images/memento_logo.png'),
            ),
            const SizedBox(height: 20),
            Text(
              userData['full_name'],
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 30),
            _buildInfoCard('Email', userData['email']),
            _buildInfoCard('Age', userData['age'].toString()),
            _buildInfoCard('Gender', userData['gender'].toString()),
            _buildInfoCard('Subscription', userData['subscription']),
            const SizedBox(height: 30),

            // Calendar
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16),
              child: Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  'Select a Day',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              height: 50,
              child: ListView.builder(
                scrollDirection: Axis.horizontal,
                itemCount: recentDays.length,
                itemBuilder: (context, index) {
                  final date = recentDays[index];
                  final formatted = DateFormat('EEE\ndd').format(date);
                  final isSelected = date == selectedDay;

                  return GestureDetector(
                    onTap: () {
                      setState(() {
                        selectedDay = date;
                      });
                    },
                    child: Container(
                      margin: const EdgeInsets.symmetric(horizontal: 8),
                      padding: const EdgeInsets.symmetric(
                        vertical: 8,
                        horizontal: 12,
                      ),
                      decoration: BoxDecoration(
                        color: isSelected ? Colors.blue : Colors.grey[200],
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Center(
                        child: Text(
                          formatted,
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                            color: isSelected ? Colors.white : Colors.black,
                          ),
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 24),

            // Activities
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16),
              child: Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  'Activities',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
              ),
            ),
            const SizedBox(height: 12),
            ...dummyActivities.map(_buildActivityCard),
            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }
}

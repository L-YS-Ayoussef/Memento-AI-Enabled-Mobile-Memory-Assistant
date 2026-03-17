import 'package:flutter/material.dart';
import '/widgets/custom_appbar.dart';
import 'subscription_details_page.dart';
import '../widgets/memento_drawer.dart';

class SubscriptionsPage extends StatelessWidget {
  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();
  SubscriptionsPage({Key? key}) : super(key: key);

  List<Map<String, dynamic>> get subscriptions => [
    {
      'plan_name': 'Basic',
      'short_description':
      'Free voice mode and offline reminders. Passive mode limited to 2 hrs/day.',
      'price': 'Free',
      'image': 'assets/images/basic.png',
    },
    {
      'plan_name': 'Plus',
      'short_description':
      'Unlimited passive mode, location triggers, Gmail & Calendar sync.',
      'price': '\$30.00 / month',
      'image': 'assets/images/standard.png',
    },
  ];

  

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: _scaffoldKey,
      appBar: CustomAppBar(
        title: 'Subscriptions',
        scaffoldKey: _scaffoldKey, 
      ),
      drawer: const MementoDrawer(),
      body: ListView.builder(
        itemCount: subscriptions.length,
        itemBuilder: (context, index) {
          final sub = subscriptions[index];
          return GestureDetector(
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => SubscriptionDetailsPage(subscription: sub),
                ),
              );
            },
            child: Card(
              margin: const EdgeInsets.all(16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              elevation: 4,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    // Text
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            sub['plan_name'],
                            style: const TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            sub['short_description'],
                            style: const TextStyle(fontSize: 14),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            'Price: ${sub['price']}',
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: Colors.blue,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 16),
                    // Image
                    ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: Image.asset(
                        sub['image'],
                        height: 80,
                        width: 80,
                        fit: BoxFit.cover,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

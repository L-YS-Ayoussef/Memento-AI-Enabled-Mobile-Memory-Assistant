import 'package:flutter/material.dart';
import 'package:animated_text_kit/animated_text_kit.dart';

class QueryPage extends StatefulWidget {
  final TextEditingController queryController;
  final bool isListeningQuery;
  final bool showStopQueryButton;
  final bool showSendButton;
  final VoidCallback onStartListening;
  final Future<void> Function() onStopListening;
  final Future<void> Function() onSendQuery;

  const QueryPage({
    super.key,
    required this.queryController,
    required this.isListeningQuery,
    required this.showStopQueryButton,
    required this.onStartListening,
    required this.onStopListening,
    required this.onSendQuery,
    required this.showSendButton,
  });

  @override
  State<QueryPage> createState() => QueryPageState();
}

class QueryPageState extends State<QueryPage> {
  final List<Map<String, dynamic>> replies = [];
  bool isLoading = false;

  void addReply(String text, {required bool isUser}) {
    setState(() {
      replies.add({"text": text, "isUser": isUser});
      isLoading = isUser;
    });
  }

  void setLoading(bool value) {
    setState(() {
      isLoading = value;
    });
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Column(
        children: [
          // ───── Logo + Header + Passive Mode (Stacked) ─────
          Stack(
            children: [
              Padding(
                padding: const EdgeInsets.only(top: 40),
                child: Column(
                  children: [
                    ClipOval(
                      child: Image.asset(
                        'assets/images/memento_logo.png',
                        height: 160,
                        width: 160,
                        fit: BoxFit.cover,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Center(
                      child: AnimatedTextKit(
                        isRepeatingAnimation: false,
                        totalRepeatCount: 1,
                        animatedTexts: [
                          TypewriterAnimatedText(
                            'Life Remembers Itself!',
                            textStyle: const TextStyle(
                              fontSize: 24,
                              fontWeight: FontWeight.w500,
                            ),
                            speed: const Duration(milliseconds: 100),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
      
              // ✅ Passive Mode top-right
              const Positioned(
                right: 16,
                top: 10,
                child: Text(
                  'Passive Mode',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    color: Colors.black87,
                  ),
                ),
              ),
            ],
          ),
      
          const SizedBox(height: 8),
      
          // ───── Replies List ─────
          Expanded(
            child: ListView.builder(
              reverse: true,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              itemCount: replies.length,
              itemBuilder: (context, index) {
                final reply = replies[index];
                final isUser = reply['isUser'] == true;
                final alignment =
                    isUser ? Alignment.centerRight : Alignment.centerLeft;
                final bubbleColor =
                    isUser
                        ? const Color.fromARGB(255, 174, 204, 238)
                        : Colors.grey.shade300;
      
                return Container(
                  alignment: alignment,
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Card(
                    color: bubbleColor,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 8,
                      ),
                      child: Text(
                        reply['text'],
                        style: const TextStyle(fontSize: 15),
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
      
          // ───── Bottom Input Area ─────
          Container(
            padding: const EdgeInsets.all(12),
            margin: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.grey[100],
              borderRadius: BorderRadius.circular(16),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 8,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                TextField(
                  controller: widget.queryController,
                  style: const TextStyle(fontSize: 16),
                  decoration: InputDecoration(
                    hintText: 'Type your query...',
                    hintStyle: const TextStyle(
                      color: Colors.grey,
                      fontSize: 16,
                      fontWeight: FontWeight.w400,
                    ),
                    filled: true,
                    fillColor: Colors.white,
                    contentPadding: const EdgeInsets.symmetric(
                      vertical: 14,
                      horizontal: 16,
                    ),
                    border: InputBorder.none,
                    enabledBorder: InputBorder.none,
                    focusedBorder: InputBorder.none,
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    if (!widget.showStopQueryButton)
                      ElevatedButton(
                        onPressed:
                            widget.isListeningQuery
                                ? null
                                : widget.onStartListening,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.black,
                          shape: const CircleBorder(),
                          padding: const EdgeInsets.all(14),
                        ),
                        child: const Icon(
                          Icons.mic_none_outlined,
                          color: Colors.white,
                        ),
                      ),
                    if (widget.showStopQueryButton)
                      ElevatedButton(
                        onPressed: widget.onStopListening,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.red,
                          shape: const CircleBorder(),
                          padding: const EdgeInsets.all(14),
                        ),
                        child: const Icon(
                          Icons.stop_circle_outlined,
                          color: Colors.white,
                        ),
                      ),
                    if (widget.showSendButton) ...[
                      const SizedBox(width: 8),
                      ElevatedButton(
                        onPressed: () async {
                          setLoading(true);
                          await widget.onSendQuery();
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.blue,
                          shape: const CircleBorder(),
                          padding: const EdgeInsets.all(14),
                        ),
                        child: const Icon(Icons.send, color: Colors.white),
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

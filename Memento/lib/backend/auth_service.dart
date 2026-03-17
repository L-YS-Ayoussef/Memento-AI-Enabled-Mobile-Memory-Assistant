import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;

class AuthService {

  Future<bool> signupUser({
    required String fullName,
    required int age,
    required String email,
    required String password,
    required String gender,
  }) async {
    try {

      final Uri url = Uri.parse(
        'https://memento-avdxhuanejbycxfm.italynorth-01.azurewebsites.net/signup',
      ); 
      final Map<String, String> body = {
        "email": email,
        "password": password,
        "gender": gender.toLowerCase(),
        "full_name": fullName,
        "age": age.toString(),
      };
      print(body);

      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: body,
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        final data = jsonDecode(response.body);
        final accessToken = data['access_token'];

        if (accessToken != null) {
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString('token', 'Bearer $accessToken');
          final now = DateTime.now().toIso8601String();
          await prefs.setString('token_issue_date', now);
          await prefs.setBool('token_validity', true);
          return true;
        }
      } else {
        print('Signup failed: ${response.body}');
      }
      return false;
    } catch (e) {
      print('Error signing up user: $e');
      return false;
    }
  }

  Future<bool> loginUser({
    required String username,
    required String password,
  }) async {
    try {
      final Uri url = Uri.parse(
        'https://memento-avdxhuanejbycxfm.italynorth-01.azurewebsites.net/login',
      ); 

      final Map<String, String> body = {
        "username": username,
        "password": password,
      };

      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: body,
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final accessToken = data['access_token'];

        if (accessToken != null) {
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString('token', 'Bearer $accessToken');
          final now = DateTime.now().toIso8601String();
          await prefs.setString('token_issue_date', now);
          await prefs.setBool('token_validity', true);
          return true;
        } else {
          print('No access token in response');
        }
      } else {
        print('Login failed: ${response.body}');
      }
      return false;
    } catch (e) {
      print('Error logging in user: $e');
      return false;
    }
  }
}

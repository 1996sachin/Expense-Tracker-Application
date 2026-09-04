import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:google_sign_in/google_sign_in.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'config.dart';

class ApiService {
  static String _accessToken = '';

  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('${apiBaseUrl}auth/login/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    final data = _decode(response);
    if (response.statusCode != 200) {
      throw ApiException(data['detail']?.toString() ?? 'Unable to sign in.');
    }
    final preferences = await SharedPreferences.getInstance();
    _accessToken = data['access']?.toString() ?? '';
    await preferences.setString('access', _accessToken);
    await preferences.setString('refresh', data['refresh']?.toString() ?? '');
    return data;
  }

  Future<void> register({required String username, required String email, required String password}) async {
    final response = await http.post(
      Uri.parse('${apiBaseUrl}auth/register/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'username': username, 'email': email, 'password': password}),
    );
    final data = _decode(response);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final firstError = data.values.isNotEmpty ? data.values.first : null;
      throw ApiException(firstError is List ? firstError.first.toString() : data['detail']?.toString() ?? 'Unable to create account.');
    }
  }

  Future<Map<String, dynamic>> googleLogin() async {
    final account = await GoogleSignIn(serverClientId: googleWebClientId, scopes: ['email']).signIn();
    if (account == null) throw const ApiException('Google sign-in was cancelled.');
    final token = (await account.authentication).idToken;
    if (token == null || token.isEmpty) throw const ApiException('Google did not return a valid credential.');
    final response = await http.post(Uri.parse('${apiBaseUrl}auth/google/'), headers: {'Content-Type': 'application/json'}, body: jsonEncode({'credential': token}));
    final data = _decode(response);
    if (response.statusCode != 200) throw ApiException(data['detail']?.toString() ?? 'Google sign-in failed.');
    final preferences = await SharedPreferences.getInstance();
    _accessToken = data['access']?.toString() ?? '';
    await preferences.setString('access', _accessToken);
    await preferences.setString('refresh', data['refresh']?.toString() ?? '');
    return data;
  }

  Future<void> loadToken() async {
    final preferences = await SharedPreferences.getInstance();
    _accessToken = preferences.getString('access') ?? '';
  }

  Future<bool> hasSession() async {
    final preferences = await SharedPreferences.getInstance();
    return (preferences.getString('access') ?? '').isNotEmpty;
  }

  Future<void> logout() async {
    final preferences = await SharedPreferences.getInstance();
    final refresh = preferences.getString('refresh');
    if (refresh != null && refresh.isNotEmpty) {
      await http.post(Uri.parse('${apiBaseUrl}auth/logout/'), headers: _headers(), body: jsonEncode({'refresh': refresh}));
    }
    _accessToken = '';
    await preferences.remove('access');
    await preferences.remove('refresh');
  }

  Future<Map<String, dynamic>> get(String path) async {
    var response = await http.get(Uri.parse('$apiBaseUrl$path'), headers: _headers());
    if (response.statusCode == 401 && await _refresh()) {
      response = await http.get(Uri.parse('$apiBaseUrl$path'), headers: _headers());
    }
    final data = _decode(response);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ApiException(data['detail']?.toString() ?? 'Request failed.');
    }
    return data;
  }

  Future<Map<String, dynamic>> post(String path, Map<String, dynamic> body) async {
    final response = await http.post(Uri.parse('$apiBaseUrl$path'), headers: _headers(), body: jsonEncode(body));
    final data = _decode(response);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final firstError = data.values.isNotEmpty ? data.values.first : null;
      throw ApiException(firstError is List ? firstError.first.toString() : data['detail']?.toString() ?? 'Request failed.');
    }
    return data;
  }

  Map<String, String> _headers() => {'Authorization': 'Bearer $_accessToken', 'Content-Type': 'application/json'};

  Future<bool> _refresh() async {
    final preferences = await SharedPreferences.getInstance();
    final refresh = preferences.getString('refresh');
    if (refresh == null || refresh.isEmpty) return false;
    final response = await http.post(Uri.parse('${apiBaseUrl}auth/refresh/'), headers: {'Content-Type': 'application/json'}, body: jsonEncode({'refresh': refresh}));
    if (response.statusCode != 200) return false;
    _accessToken = _decode(response)['access']?.toString() ?? '';
    await preferences.setString('access', _accessToken);
    return _accessToken.isNotEmpty;
  }

  Map<String, dynamic> _decode(http.Response response) {
    if (response.body.isEmpty) return <String, dynamic>{};
    final data = jsonDecode(response.body);
    return data is Map<String, dynamic> ? data : <String, dynamic>{};
  }
}

class ApiException implements Exception {
  const ApiException(this.message);
  final String message;
  @override
  String toString() => message;
}

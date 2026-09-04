import 'package:flutter/material.dart';

import 'api_service.dart';

const plum = Color(0xFF29224D);
const violet = Color(0xFF6D5DFC);
const muted = Color(0xFF70778A);

void main() => runApp(const PocketlyApp());

class PocketlyApp extends StatelessWidget {
  const PocketlyApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
        debugShowCheckedModeBanner: false,
        title: 'Pocketly',
        theme: ThemeData(
          useMaterial3: true,
          colorScheme: ColorScheme.fromSeed(seedColor: violet),
          scaffoldBackgroundColor: const Color(0xFFF7F8FC),
        ),
        home: const BootstrapPage(),
      );
}

class BootstrapPage extends StatefulWidget {
  const BootstrapPage({super.key});
  @override
  State<BootstrapPage> createState() => _BootstrapPageState();
}

class _BootstrapPageState extends State<BootstrapPage> {
  final api = ApiService();
  bool? signedIn;
  @override
  void initState() { super.initState(); _check(); }
  Future<void> _check() async {
    await api.loadToken();
    final value = await api.hasSession();
    if (mounted) setState(() => signedIn = value);
  }
  @override
  Widget build(BuildContext context) {
    if (signedIn == null) return const Scaffold(body: Center(child: CircularProgressIndicator(color: violet)));
    return signedIn! ? Workspace(api: api) : LoginPage(api: api, onLogin: () => setState(() => signedIn = true));
  }
}

class LoginPage extends StatefulWidget {
  const LoginPage({required this.api, required this.onLogin, super.key});
  final ApiService api;
  final VoidCallback onLogin;
  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final username = TextEditingController();
  final email = TextEditingController();
  final password = TextEditingController();
  bool loading = false, hidden = true, creatingAccount = false;
  String? error;
  @override
  void dispose() { username.dispose(); email.dispose(); password.dispose(); super.dispose(); }
  Future<void> _submit() async {
    if ((creatingAccount && username.text.trim().isEmpty) || !email.text.contains('@') || password.text.length < 8) {
      setState(() => error = creatingAccount ? 'Enter a username, valid email, and password of at least 8 characters.' : 'Enter a valid email and password of at least 8 characters.');
      return;
    }
    setState(() { loading = true; error = null; });
    try {
      if (creatingAccount) {
        await widget.api.register(username: username.text.trim(), email: email.text.trim(), password: password.text);
      }
      final data = await widget.api.login(email.text.trim(), password.text);
      if (data['mfa_required'] == true) {
        if (mounted) setState(() => error = 'MFA is required. MFA screen is next.');
      } else if (mounted) {
        widget.onLogin();
      }
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }
  Future<void> _googleLogin() async {
    setState(() { loading = true; error = null; });
    try {
      final data = await widget.api.googleLogin();
      if (data['mfa_required'] == true) {
        if (mounted) setState(() => error = 'MFA is required.');
      } else if (mounted) {
        widget.onLogin();
      }
    } catch (e) {
      if (mounted) setState(() => error = e.toString());
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }
  @override
  Widget build(BuildContext context) => Scaffold(
        body: Stack(children: [
          Positioned(top: -100, left: -80, child: _orb(270, const Color(0xFFB7A9FF))),
          Positioned(bottom: -100, right: -80, child: _orb(240, const Color(0xFFD8C7FF))),
          SafeArea(child: Center(child: SingleChildScrollView(padding: const EdgeInsets.all(20), child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 440),
            child: Card(elevation: 0, color: Colors.white.withValues(alpha: .95), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(21)), child: Padding(
              padding: const EdgeInsets.fromLTRB(25, 30, 25, 25),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('pocketly', style: TextStyle(fontSize: 34, fontWeight: FontWeight.w700, color: plum)),
                const SizedBox(height: 36),
                Text(creatingAccount ? 'Create your account' : 'Welcome back', style: const TextStyle(fontSize: 27, fontWeight: FontWeight.w700, color: plum)),
                const SizedBox(height: 8),
                Text(creatingAccount ? 'Start managing your money with Pocketly' : 'Sign in to continue to Pocketly', style: const TextStyle(color: muted)),
                const SizedBox(height: 28),
                if (creatingAccount) ...[_field('Username', username, Icons.person_outline, false), const SizedBox(height: 17)],
                _field('Email address', email, Icons.mail_outline, false),
                const SizedBox(height: 17),
                _field('Password', password, Icons.lock_outline, true),
                Align(alignment: Alignment.centerRight, child: TextButton(onPressed: () {}, child: const Text('Forgot password?', style: TextStyle(color: violet)))),
                if (error != null) Padding(padding: const EdgeInsets.only(bottom: 12), child: Text(error!, style: const TextStyle(color: Colors.red, fontSize: 12))),
                SizedBox(width: double.infinity, height: 52, child: FilledButton(onPressed: loading ? null : _submit, style: FilledButton.styleFrom(backgroundColor: violet, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(11))), child: loading ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) : const Text('Sign in'))),
                const SizedBox(height: 18),
                Row(children: const [Expanded(child: Divider()), Padding(padding: EdgeInsets.symmetric(horizontal: 10), child: Text('OR', style: TextStyle(color: muted, fontSize: 11, fontWeight: FontWeight.w700))), Expanded(child: Divider())]),
                const SizedBox(height: 16),
                SizedBox(width: double.infinity, height: 50, child: OutlinedButton.icon(onPressed: loading ? null : _googleLogin, icon: const Text('G', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: Color(0xFF4285F4))), label: const Text('Continue with Google'), style: OutlinedButton.styleFrom(foregroundColor: plum, side: const BorderSide(color: Color(0xFFDCDDEA)), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(11))))),
                const SizedBox(height: 10),
                Center(child: TextButton(onPressed: loading ? null : () => setState(() { creatingAccount = !creatingAccount; error = null; }), child: Text(creatingAccount ? 'Already have an account? Sign in' : 'Create an account', style: const TextStyle(color: violet, fontWeight: FontWeight.w600)))),
              ]),
            )),
          )))),
        ]),
      );
  Widget _field(String label, TextEditingController controller, IconData icon, bool secret) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label, style: const TextStyle(color: plum, fontSize: 13, fontWeight: FontWeight.w600)), const SizedBox(height: 7),
        TextField(controller: controller, obscureText: secret && hidden, keyboardType: secret ? TextInputType.text : TextInputType.emailAddress, decoration: InputDecoration(hintText: secret ? 'Your password' : 'you@example.com', prefixIcon: Icon(icon, color: const Color(0xFF8A83AB)), suffixIcon: secret ? IconButton(onPressed: () => setState(() => hidden = !hidden), icon: Icon(hidden ? Icons.visibility_outlined : Icons.visibility_off_outlined)) : null, filled: true, fillColor: Colors.white, border: OutlineInputBorder(borderRadius: BorderRadius.circular(11), borderSide: const BorderSide(color: Color(0xFFDCDDEA))), enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(11), borderSide: const BorderSide(color: Color(0xFFDCDDEA))), focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(11), borderSide: const BorderSide(color: violet, width: 1.5))))
      ]);
  Widget _orb(double size, Color color) => Container(width: size, height: size, decoration: BoxDecoration(shape: BoxShape.circle, color: color.withValues(alpha: .25)));
}

class Workspace extends StatefulWidget {
  const Workspace({required this.api, super.key});
  final ApiService api;
  @override
  State<Workspace> createState() => _WorkspaceState();
}

class _WorkspaceState extends State<Workspace> {
  int tab = 0;
  final titles = ['Overview', 'Accounts', 'Transactions', 'Budgets', 'Goals'];
  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text(titles[tab], style: const TextStyle(color: plum, fontWeight: FontWeight.w700)), actions: [
          IconButton(onPressed: () {}, icon: const Icon(Icons.notifications_none)),
          IconButton(onPressed: () async { await widget.api.logout(); if (mounted) Navigator.of(context).pushAndRemoveUntil(MaterialPageRoute(builder: (_) => const BootstrapPage()), (_) => false); }, icon: const Icon(Icons.logout_outlined)),
        ], backgroundColor: Colors.transparent),
        body: IndexedStack(index: tab, children: [
          OverviewPage(api: widget.api),
          ResourcePage(api: widget.api, endpoint: 'accounts/', title: 'Accounts', icon: Icons.account_balance_wallet_outlined),
          ResourcePage(api: widget.api, endpoint: 'transactions/?ordering=-date', title: 'Transactions', icon: Icons.swap_vert_rounded),
          ResourcePage(api: widget.api, endpoint: 'budgets/', title: 'Budgets', icon: Icons.pie_chart_outline),
          ResourcePage(api: widget.api, endpoint: 'goals/', title: 'Goals', icon: Icons.flag_outlined),
        ]),
        bottomNavigationBar: NavigationBar(selectedIndex: tab, onDestinationSelected: (value) => setState(() => tab = value), destinations: const [
          NavigationDestination(icon: Icon(Icons.grid_view_outlined), selectedIcon: Icon(Icons.grid_view), label: 'Overview'),
          NavigationDestination(icon: Icon(Icons.account_balance_wallet_outlined), label: 'Accounts'),
          NavigationDestination(icon: Icon(Icons.swap_horiz_outlined), label: 'Activity'),
          NavigationDestination(icon: Icon(Icons.pie_chart_outline), label: 'Budgets'),
          NavigationDestination(icon: Icon(Icons.flag_outlined), label: 'Goals'),
        ]),
      );
}

class OverviewPage extends StatelessWidget {
  const OverviewPage({required this.api, super.key});
  final ApiService api;
  @override
  Widget build(BuildContext context) => FutureBuilder<List<Map<String, dynamic>>>(future: Future.wait([api.get('accounts/summary/'), api.get('transactions/?ordering=-date')]), builder: (context, snapshot) {
    if (snapshot.hasError) return Center(child: Text(snapshot.error.toString()));
    if (!snapshot.hasData) return const Center(child: CircularProgressIndicator(color: violet));
    final summary = snapshot.data![0], transactions = _items(snapshot.data![1]);
    return RefreshIndicator(onRefresh: () async { await Future.wait([api.get('accounts/summary/'), api.get('transactions/?ordering=-date')]); }, child: ListView(padding: const EdgeInsets.fromLTRB(18, 8, 18, 24), children: [
      const Text('FINANCIAL OVERVIEW', style: TextStyle(color: muted, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 1.2)), const SizedBox(height: 4), const Text('Good morning', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w700, color: plum)), const SizedBox(height: 18),
      Container(padding: const EdgeInsets.all(22), decoration: BoxDecoration(gradient: const LinearGradient(colors: [plum, Color(0xFF594BD7)]), borderRadius: BorderRadius.circular(17)), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [const Text('Total net worth', style: TextStyle(color: Color(0xFFC9C4FF))), const SizedBox(height: 8), Text(_money(summary['net_worth']), style: const TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.w700)), Text('${(summary['accounts'] as List?)?.length ?? 0} active accounts', style: const TextStyle(color: Color(0xFFC9C4FF)))])),
      const SizedBox(height: 22), const Text('Recent transactions', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: plum)), const SizedBox(height: 10),
      if (transactions.isEmpty) const _EmptyState() else ...transactions.take(6).map((item) => _TransactionTile(item: item)),
    ]));
  });
}

class ResourcePage extends StatefulWidget {
  const ResourcePage({required this.api, required this.endpoint, required this.title, required this.icon, super.key});
  final ApiService api; final String endpoint, title; final IconData icon;
  @override State<ResourcePage> createState() => _ResourcePageState();
}

class _ResourcePageState extends State<ResourcePage> {
  bool saving = false;
  Future<void> _create() async {
    final fields = <String, TextEditingController>{};
    final isAccount = widget.title == 'Accounts';
    final isTransaction = widget.title == 'Transactions';
    final isBudget = widget.title == 'Budgets';
    final labels = isAccount ? ['name', 'bank_name', 'opening_balance'] : isTransaction ? ['amount', 'date', 'account', 'note'] : isBudget ? ['category', 'period_start', 'period_end', 'limit_amount'] : ['name', 'target_amount', 'target_date'];
    for (final label in labels) fields[label] = TextEditingController(text: label.contains('date') ? DateTime.now().toIso8601String().substring(0, 10) : '');
    final form = await showDialog<bool>(context: context, builder: (context) => AlertDialog(title: Text('Add ${widget.title.substring(0, widget.title.length - 1).toLowerCase()}'), content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: fields.entries.map((entry) => Padding(padding: const EdgeInsets.only(bottom: 10), child: TextField(controller: entry.value, keyboardType: ['amount', 'opening_balance', 'limit_amount', 'target_amount', 'account', 'category'].contains(entry.key) ? TextInputType.number : TextInputType.text, decoration: InputDecoration(labelText: entry.key.replaceAll('_', ' '), border: const OutlineInputBorder())))).toList()), actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')), FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Save'))]));
    if (form != true) { for (final controller in fields.values) controller.dispose(); return; }
    setState(() => saving = true);
    try {
      final body = <String, dynamic>{for (final entry in fields.entries if entry.value.text.isNotEmpty) entry.key: ['amount', 'opening_balance', 'limit_amount', 'target_amount', 'account', 'category'].contains(entry.key) ? (double.tryParse(entry.value.text) ?? int.tryParse(entry.value.text)) : entry.value.text};
      if (isTransaction) body['type'] = 'expense';
      if (isAccount) { body['account_type'] = 'checking'; body['currency'] = 'NPR'; }
      await widget.api.post(widget.endpoint, body);
      if (mounted) { setState(() {}); ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Saved successfully'))); }
    } catch (error) { if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error.toString()))); }
    finally { for (final controller in fields.values) controller.dispose(); if (mounted) setState(() => saving = false); }
  }
  @override
  Widget build(BuildContext context) => FutureBuilder<Map<String, dynamic>>(future: widget.api.get(widget.endpoint), builder: (context, snapshot) {
    if (snapshot.hasError) return Center(child: Padding(padding: const EdgeInsets.all(20), child: Text(snapshot.error.toString())));
    if (!snapshot.hasData) return const Center(child: CircularProgressIndicator(color: violet));
    final items = _items(snapshot.data!);
    return RefreshIndicator(onRefresh: () async { await widget.api.get(widget.endpoint); }, child: ListView(padding: const EdgeInsets.all(18), children: [
      Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(widget.title.toUpperCase(), style: const TextStyle(color: muted, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 1.2)), const SizedBox(height: 4), Text('${items.length} items', style: const TextStyle(color: plum, fontSize: 26, fontWeight: FontWeight.w700))]), FilledButton.icon(onPressed: saving ? null : _create, icon: const Icon(Icons.add), label: const Text('Add'))]), const SizedBox(height: 16),
      if (items.isEmpty) const _EmptyState() else ...items.map((item) => Card(margin: const EdgeInsets.only(bottom: 10), elevation: 0, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(13), side: const BorderSide(color: Color(0xFFE8EAF1))), child: ListTile(leading: CircleAvatar(backgroundColor: const Color(0xFFF0EDFF), child: Icon(widget.icon, color: violet)), title: Text(_name(item), style: const TextStyle(fontWeight: FontWeight.w700, color: plum)), subtitle: Text(_subtitle(item)), trailing: Text(_amount(item), style: const TextStyle(fontWeight: FontWeight.w700, color: plum))))
    ]));
  });
}

class _TransactionTile extends StatelessWidget {
  const _TransactionTile({required this.item}); final Map<String, dynamic> item;
  @override Widget build(BuildContext context) => ListTile(contentPadding: const EdgeInsets.symmetric(vertical: 3), leading: const CircleAvatar(backgroundColor: Color(0xFFF0EDFF), child: Icon(Icons.receipt_long_outlined, color: violet)), title: Text(_name(item), style: const TextStyle(fontWeight: FontWeight.w600, color: plum)), subtitle: Text(item['date']?.toString() ?? '', style: const TextStyle(color: muted, fontSize: 12)), trailing: Text('${item['type'] == 'expense' ? '-' : '+'}${_money(item['amount'])}', style: TextStyle(fontWeight: FontWeight.w700, color: item['type'] == 'expense' ? const Color(0xFFE0647B) : const Color(0xFF21A77F))));
}
class _EmptyState extends StatelessWidget { const _EmptyState(); @override Widget build(BuildContext context) => const Padding(padding: EdgeInsets.all(32), child: Center(child: Text('No data yet', style: TextStyle(color: muted)))); }
List<Map<String, dynamic>> _items(Map<String, dynamic> data) => ((data['results'] ?? data) as List?)?.whereType<Map<String, dynamic>>().toList() ?? [];
String _name(Map<String, dynamic> item) => (item['name'] ?? item['note'] ?? item['category_name'] ?? 'Untitled').toString();
String _subtitle(Map<String, dynamic> item) => (item['bank_name'] ?? item['date'] ?? item['type'] ?? 'Pocketly').toString();
String _amount(Map<String, dynamic> item) => item['current_balance'] != null ? _money(item['current_balance']) : item['amount'] != null ? _money(item['amount']) : item['limit_amount'] != null ? _money(item['limit_amount']) : '';
String _money(dynamic value) => 'NPR ${double.tryParse(value?.toString() ?? '0')?.toStringAsFixed(2) ?? '0.00'}';

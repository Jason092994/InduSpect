// InduSpect AI smoke test
//
// Verifies that the InduSpectApp widget can be instantiated and
// renders without errors.

import 'package:flutter_test/flutter_test.dart';
import 'package:induspect_ai/main.dart';

void main() {
  testWidgets('InduSpectApp renders without error', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const InduSpectApp());
    await tester.pumpAndSettle();

    // Verify that InduSpect AI title appears somewhere in the widget tree
    expect(find.textContaining('InduSpect'), findsWidgets);
  });
}

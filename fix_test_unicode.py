"""
Fix Unicode emoji characters in test files for Windows compatibility
"""
import os
import glob

# Unicode replacements
replacements = {
    '✅': '[PASS]',
    '❌': '[FAIL]',
    '⚠️': '[WARN]',
    '🎉': '[SUCCESS]',
    '🧹': '[CLEANUP]',
    '👤': '[USER]',
    '📝': '[CREATE]',
    '📍': '[POSITION]',
    '🚨': '[ALERT]',
    '✓': '[OK]',
}

# Find all test files
test_files = glob.glob('test_*.py')

print("Fixing Unicode characters in test files...")
print("=" * 60)

for filepath in test_files:
    print(f"\nProcessing: {filepath}")
    
    try:
        # Read file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Track changes
        changes = 0
        original_content = content
        
        # Replace Unicode characters
        for unicode_char, ascii_replacement in replacements.items():
            if unicode_char in content:
                count = content.count(unicode_char)
                content = content.replace(unicode_char, ascii_replacement)
                changes += count
                print(f"  - Replaced {count} occurrence(s) of '{unicode_char}' with '{ascii_replacement}'")
        
        # Write back if changes were made
        if changes > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  [PASS] Fixed {changes} Unicode character(s)")
        else:
            print(f"  [SKIP] No Unicode characters found")
            
    except Exception as e:
        print(f"  [FAIL] Error: {e}")

print("\n" + "=" * 60)
print("Unicode fix complete!")

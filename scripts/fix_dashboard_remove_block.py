"""Remove the leftover explanation block from dashboard.html."""
path = r"c:\IoT-security-app-python\web\dashboard.html"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()
# Remove lines 133-141 (1-based) = index 132-140. Content: ul, li, li, li, /ul, p, /div, /div, blank
to_remove = set(range(132, 141))
new_lines = [line for i, line in enumerate(lines) if i not in to_remove]
with open(path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)
print("Removed orphaned block.")

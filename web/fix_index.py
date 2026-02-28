# One-off fix for index.html
path = "index.html"
with open(path, "r", encoding="utf-8") as f:
    s = f.read()
# Fix paragraph (curly or straight apostrophe)
for old in [
    "Monitor your\u2019ve created an account, you can add devices, receive alerts, and post device heartbeats.",
    "Monitor your've created an account, you can add devices, receive alerts, and post device heartbeats.",
]:
    s = s.replace(old, "Monitor your smart home devices, get instant alerts when something goes offline, and manage everything in one place.")
# Remove second card block
marker = "<h2>REMOVE_THIS_CARD</h2>"
i = s.find(marker)
if i != -1:
    start = s.rfind('<div class="card">', 0, i)
    # After this card we have </div></div> (card then grid). Find end of this card.
    j = s.find("</ul>", i) + 5
    j = s.find("</div>", j) + 6   # card's closing div
    s = s[:start] + s[j:]
with open(path, "w", encoding="utf-8") as f:
    f.write(s)
print("Fixed index.html")

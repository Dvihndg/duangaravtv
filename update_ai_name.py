with open("admin.html", "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("Trợ lý GarageAI", "AI quản trị")
c = c.replace("Trợ lý AI Garage", "AI quản trị")
with open("admin.html", "w", encoding="utf-8") as f:
    f.write(c)

with open("app.js", "r", encoding="utf-8") as f:
    c = f.read()
c = c.replace("Trợ lý GarageAI", "AI quản trị")
c = c.replace("Trợ lý AI Garage", "AI quản trị")
with open("app.js", "w", encoding="utf-8") as f:
    f.write(c)

print("Changed AI names to AI quản trị")

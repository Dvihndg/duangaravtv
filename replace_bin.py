with open("admin.html", "rb") as f:
    c = f.read()
c = c.replace("Trợ lý GarageAI".encode("utf-8"), "AI quản trị".encode("utf-8"))
c = c.replace("Trợ lý AI Garage".encode("utf-8"), "AI quản trị".encode("utf-8"))
with open("admin.html", "wb") as f:
    f.write(c)

with open("app.js", "rb") as f:
    c = f.read()
c = c.replace("Trợ lý GarageAI".encode("utf-8"), "AI quản trị".encode("utf-8"))
c = c.replace("Trợ lý AI Garage".encode("utf-8"), "AI quản trị".encode("utf-8"))
with open("app.js", "wb") as f:
    f.write(c)

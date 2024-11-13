from functools import wraps
from flask import Flask, jsonify, render_template, request
import json
import os
import random
app = Flask(__name__)

file_path = os.path.join(os.path.dirname(__file__), "tasks.json")



if not os.path.exists(file_path):
    with open(file_path, "w") as file:
        json.dump([], file)

def load_tasks():
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return []

def save_tasks(task_list):
    with open(file_path, "w") as file:
        json.dump(task_list, file, indent=4)

def complete_tasks(task_list):
    with open(file_path, "w") as file:
        json.dump(task_list, file, indent = 4)

def auth(func):
    @wraps(func)
    def deco_func(*args, **kwargs):
        auth_password = request.headers.get("x-password")
        
        if not auth_password:
            return jsonify({"error": "password required"}), 401

        if auth_password == "123":
            return func(*args, **kwargs)
        else:
            return jsonify({"error": "invalid password"}), 403

    return deco_func


@app.route("/TODO/<int:task_id>", methods=["DELETE"])
@auth
def delete_task(task_id):
    task_list = load_tasks()

    for task in task_list[:]:
        if task["id"] == task_id:
            task_list.remove(task)
            save_tasks(task_list)
            return jsonify({"success": True}), 200
    return jsonify({"error": "Task not found"}), 404
    
@app.route("/TODO/<int:task_id>", methods=["PUT"])
def update_status(task_id):
    task_list = load_tasks()

    for task in task_list:
        if task["id"] == task_id:
            task["status"] = "completed" if task["status"] == "pending" else "pending"
            break
    else: 
        return jsonify({"error": "Task not found"}), 404
    
    save_tasks(task_list)
    
    return jsonify({"success": True, "status": task["status"]})

@app.route("/todo", methods=["GET", "POST"])
@app.route("/json", methods=["GET", "POST"])
def get_tasks():
    
    task_list_unsorted = load_tasks()
    task_list = sorted(task_list_unsorted, key=lambda x: len(x['status']))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')

        if title and description and category:
            task = {
                'title': title,
                'description': description,
                'category': category,
                'status': "pending",
                'id': random.randint(0, 999) #  TODO: CHECKA EFTER DUBBLETTER
            }
            task_list.append(task)
            save_tasks(task_list)
            return render_template("TODO.html", title="TODO", tasks=task_list)
        else:
            return jsonify({"error": "Missing title, description, or category"}), 400
        
    elif request.method == 'GET':
        return render_template("TODO.html", title="TODO", show_paragraph=True, tasks=task_list)
    
    return jsonify({"error": "Method not allowed"}), 405 #för PUT OCH DELETE

@app.route("/todo/categories/<task_cat>", methods=["GET"])
def get_tasks_cat_sorted(task_cat):
    task_list_unsorted = load_tasks()
    task_cat_sorted = []

    for task in task_list_unsorted:
        if task['category'] == task_cat:
            task_cat_sorted.append(task)
    if task_cat_sorted == []:
        return jsonify({"error": "Error loading category"}), 300 #??? VAFAN ÄR EN PASSANDE ERRORKOD FÖR DET HÄR
    else:
        return render_template("sorted.html", title="TODO", show_paragraph=True, tasks=task_cat_sorted)

    

@app.route("/todo/categories", methods=["GET"])
def get_categories():
    cat_watcher = set()
    cat_list = []
    cat_list.clear()
    task_list = load_tasks()
    for task in task_list:
        if task['category'] not in cat_watcher:
            cat_list.append(task)
            cat_watcher.add(task['category'])

    return render_template("categories.html", title="TODO", show_paragraph=True, tasks=cat_list)

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, render_template, request, jsonify
import random
import os

# 1. 初始化 Flask 应用
app = Flask(__name__)

# 2. 定义一个函数来加载祝福语句
def load_wishes():
    """
    从 wishes.txt 文件中加载祝福，如果文件不存在，则创建并使用默认祝福。
    """
    # 定义祝福文件的路径
    wishes_path = "wishes.txt"
    
    # 默认的祝福语句列表
    default_wishes = [
        "生日快乐！愿所有美好都如期而至！",
        "祝你今天像公主一样闪耀！",
        "新的一岁，暴富暴美！",
        "愿你的每一天都充满阳光和欢笑！",
        "生日快乐，健康、开心、幸运！",
        "愿你永远年轻，永远热泪盈眶！",
        "在这个特别的日子里，祝你生日快乐，心想事成！"
    ]
    
    # 检查文件是否存在
    if not os.path.exists(wishes_path):
        try:
            # 如果不存在，就创建文件并写入默认祝福
            with open(wishes_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(default_wishes))
            print(f"'{wishes_path}' 文件已创建，并写入默认祝福。")
            return default_wishes
        except Exception as e:
            print(f"创建 '{wishes_path}' 文件失败: {e}")
            return default_wishes

    # 如果文件存在，就读取它
    try:
        with open(wishes_path, 'r', encoding='utf-8') as f:
            # 读取所有行，并过滤掉空行
            wishes = [line.strip() for line in f if line.strip()]
        # 如果文件为空，就返回默认祝福
        return wishes if wishes else default_wishes
    except Exception as e:
        print(f"读取 '{wishes_path}' 文件失败: {e}")
        return default_wishes

# 3. 定义一个路由和视图函数，用于处理网站的主页请求
@app.route('/')
def home():
    """
    当用户访问网站根目录时，返回主页。
    """
    return render_template('index.html')

# 4. 定义一个 API 接口，用于动态获取随机祝福
@app.route('/get_wish', methods=['POST'])
def get_wish():
    """
    当网页上的按钮被点击时，这个接口会被调用。
    它接收一个 JSON 数据（包含寿星名字），并返回一个随机的祝福。
    """
    # 从请求中获取 JSON 数据
    data = request.get_json()
    name = data.get('name', '亲爱的朋友') # 如果没有收到名字，就用默认值
    
    # 加载祝福列表
    wishes = load_wishes()
    
    # 随机选择一条祝福
    random_wish = random.choice(wishes)
    
    # 将名字和祝福拼接起来
    personalized_wish = f"{name}，{random_wish}"
    
    # 以 JSON 格式返回结果
    return jsonify({'wish': personalized_wish})

# 5. 运行应用
if __name__ == '__main__':
    # debug=True 表示开启调试模式，代码修改后服务器会自动重启
    app.run(debug=True)

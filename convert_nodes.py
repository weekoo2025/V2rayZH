import yaml
import json
import requests
import base64
from urllib.parse import quote, urlencode
import os

def convert_to_v2ray(proxy):
    """将单个代理配置转换为v2ray格式"""
    proxy_type = proxy.get("type", "").lower()
    
    if proxy_type == "vless":
        # VLESS格式: vless://uuid@server:port?参数&参数#备注
        params = {
            "type": "ws",
            "security": "tls" if proxy.get("tls") else "none",
            "path": proxy.get("ws-opts", {}).get("path", ""),
            "host": proxy.get("ws-opts", {}).get("headers", {}).get("Host", ""),
            "sni": proxy.get("servername", "")
        }
        
        # 移除空值参数
        params = {k: v for k, v in params.items() if v}
        
        # 确保编码正确
        server_name = quote(proxy['name'])
        params_str = urlencode(params)
        
        url = f"vless://{proxy['uuid']}@{proxy['server']}:{proxy['port']}?{params_str}#{server_name}"
        return url
        
    elif proxy_type == "trojan":
        # Trojan格式: trojan://password@server:port?参数&参数#备注
        params = {
            "type": "ws",
            "security": "tls",
            "path": proxy.get("ws-opts", {}).get("path", ""),
            "host": proxy.get("ws-opts", {}).get("headers", {}).get("Host", ""),
            "sni": proxy.get("sni", "")
        }
        
        # 移除空值参数
        params = {k: v for k, v in params.items() if v}
        
        # 确保编码正确
        server_name = quote(proxy['name'])
        params_str = urlencode(params)
        
        url = f"trojan://{proxy['password']}@{proxy['server']}:{proxy['port']}?{params_str}#{server_name}"
        return url
        
    else:
        # 不支持的类型
        return None

def generate_subscription(configs):
    """生成订阅链接内容"""
    valid_links = [link for link in configs if link is not None]
    # 确保每个链接独占一行
    content = '\n'.join(valid_links)
    # 添加一个换行确保base64编码正确
    if not content.endswith('\n'):
        content += '\n'
    return base64.b64encode(content.encode('utf-8')).decode('utf-8')

def main():
    try:
        print("开始获取YAML数据...")
        url = "https://raw.githubusercontent.com/go4sharing/sub/main/worker.yaml"
        response = requests.get(url)
        response.raise_for_status()
        yaml_data = yaml.safe_load(response.text)
        
        print(f"成功获取YAML数据，开始转换代理配置...")
        v2ray_links = []
        for proxy in yaml_data.get("proxies", []):
            link = convert_to_v2ray(proxy)
            if link:
                v2ray_links.append(link)
        
        print(f"转换完成，共有 {len(v2ray_links)} 个有效节点")
        subscription = generate_subscription(v2ray_links)
        
        print("正在写入文件...")
        with open("subscription.txt", "w", encoding='utf-8', newline='\n') as f:
            f.write(subscription)
            f.flush()
            os.fsync(f.fileno())
        
        print("文件写入完成！")
        
    except Exception as e:
        print(f"错误: {e}")
        raise  # 重新抛出异常以确保 GitHub Actions 知道任务失败

if __name__ == "__main__":
    main() 
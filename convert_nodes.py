import yaml
import json
import requests
import base64
from urllib.parse import quote, urlencode

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
        
        url = f"vless://{proxy['uuid']}@{proxy['server']}:{proxy['port']}?{urlencode(params)}#{quote(proxy['name'])}"
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
        
        url = f"trojan://{proxy['password']}@{proxy['server']}:{proxy['port']}?{urlencode(params)}#{quote(proxy['name'])}"
        return url
        
    else:
        # 不支持的类型
        return None

def generate_subscription(configs):
    """生成订阅链接内容"""
    valid_links = [link for link in configs if link is not None]
    return base64.b64encode('\n'.join(valid_links).encode()).decode()

def main():
    try:
        # 直接从URL获取YAML内容
        url = "https://raw.githubusercontent.com/go4sharing/sub/main/worker.yaml"
        response = requests.get(url)
        response.raise_for_status()
        yaml_data = yaml.safe_load(response.text)
        
        # 转换所有代理配置
        v2ray_links = []
        for proxy in yaml_data.get("proxies", []):
            link = convert_to_v2ray(proxy)
            if link:
                v2ray_links.append(link)
        
        # 生成订阅内容
        subscription = generate_subscription(v2ray_links)
        
        # 保存到文件
        with open("subscription.txt", "w") as f:
            f.write(subscription)
        
        print(f"转换完成！成功转换 {len(v2ray_links)} 个节点")
        
    except Exception as e:
        print(f"处理过程中出错: {e}")

if __name__ == "__main__":
    main() 
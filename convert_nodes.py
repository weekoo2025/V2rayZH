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
        # VLESS格式
        params = {
            "type": proxy.get("network", "tcp"),
            "security": proxy.get("security", "none"),
            "path": proxy.get("ws-opts", {}).get("path", ""),
            "host": proxy.get("ws-opts", {}).get("headers", {}).get("Host", ""),
            "sni": proxy.get("servername", "")
        }
        
        # 移除空值参数
        params = {k: v for k, v in params.items() if v}
        
        server_name = quote(proxy['name'])
        params_str = urlencode(params)
        
        url = f"vless://{proxy['uuid']}@{proxy['server']}:{proxy['port']}?{params_str}#{server_name}"
        return url
        
    elif proxy_type == "trojan":
        # Trojan格式
        params = {
            "type": proxy.get("network", "tcp"),
            "security": "tls",
            "path": proxy.get("ws-opts", {}).get("path", ""),
            "host": proxy.get("ws-opts", {}).get("headers", {}).get("Host", ""),
            "sni": proxy.get("sni", "")
        }
        
        params = {k: v for k, v in params.items() if v}
        server_name = quote(proxy['name'])
        params_str = urlencode(params)
        
        url = f"trojan://{proxy['password']}@{proxy['server']}:{proxy['port']}?{params_str}#{server_name}"
        return url
        
    elif proxy_type == "ss" or proxy_type == "shadowsocks":
        # SS格式
        method = proxy.get("cipher", "")
        password = proxy.get("password", "")
        if method and password:
            userinfo = base64.b64encode(f"{method}:{password}".encode()).decode()
            server_name = quote(proxy['name'])
            url = f"ss://{userinfo}@{proxy['server']}:{proxy['port']}#{server_name}"
            return url
            
    elif proxy_type == "vmess":
        # VMess格式
        config = {
            "v": "2",
            "ps": proxy['name'],
            "add": proxy['server'],
            "port": str(proxy['port']),
            "id": proxy.get('uuid', ""),
            "aid": str(proxy.get('alterId', 0)),
            "net": proxy.get('network', 'tcp'),
            "type": "none",
            "host": proxy.get('ws-opts', {}).get('headers', {}).get('Host', ''),
            "path": proxy.get('ws-opts', {}).get('path', ''),
            "tls": "tls" if proxy.get('tls') else ""
        }
        
        vmess_config = base64.b64encode(json.dumps(config).encode()).decode()
        return f"vmess://{vmess_config}"
    
    return None

def generate_subscription(configs):
    """生成订阅链接内容"""
    valid_links = [link for link in configs if link is not None]
    content = '\n'.join(valid_links)
    if not content.endswith('\n'):
        content += '\n'
    return base64.b64encode(content.encode('utf-8')).decode('utf-8')

def main():
    try:
        print("开始获取YAML数据...")
        
        # 获取原有源
        url1 = "https://raw.githubusercontent.com/go4sharing/sub/main/worker.yaml"
        response1 = requests.get(url1)
        response1.raise_for_status()
        yaml_data1 = yaml.safe_load(response1.text)
        
        # 获取新增源
        url2 = "https://gist.githubusercontent.com/weekoo2025/7a8bcb034d5d223384101b8c4773089a/raw/all.yaml"
        response2 = requests.get(url2)
        response2.raise_for_status()
        yaml_data2 = yaml.safe_load(response2.text)
        
        print(f"成功获取YAML数据，开始转换代理配置...")
        
        # 转换原有源的节点
        v2ray_links1 = []
        for proxy in yaml_data1.get("proxies", []):
            link = convert_to_v2ray(proxy)
            if link:
                v2ray_links1.append(link)
        
        # 转换新增源的节点
        v2ray_links2 = []
        for proxy in yaml_data2.get("proxies", []):
            link = convert_to_v2ray(proxy)
            if link:
                v2ray_links2.append(link)
        
        print(f"转换完成，源1有 {len(v2ray_links1)} 个节点，源2有 {len(v2ray_links2)} 个节点")
        
        # 生成并保存源1的订阅
        subscription1 = generate_subscription(v2ray_links1)
        with open("subscription1.txt", "w", encoding='utf-8', newline='\n') as f:
            f.write(subscription1)
            f.flush()
            os.fsync(f.fileno())
            
        # 生成并保存源2的订阅    
        subscription2 = generate_subscription(v2ray_links2)
        with open("subscription2.txt", "w", encoding='utf-8', newline='\n') as f:
            f.write(subscription2)
            f.flush()
            os.fsync(f.fileno())
            
        # 生成并保存合并的订阅
        subscription_all = generate_subscription(v2ray_links1 + v2ray_links2)
        with open("subscription.txt", "w", encoding='utf-8', newline='\n') as f:
            f.write(subscription_all)
            f.flush()
            os.fsync(f.fileno())
        
        print("文件写入完成！")
        
    except Exception as e:
        print(f"错误: {e}")
        raise

if __name__ == "__main__":
    main() 
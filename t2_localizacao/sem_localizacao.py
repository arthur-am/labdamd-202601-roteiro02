import requests

def buscar_usuario(user_id: int):
    url = f"http://192.168.10.42:8080/users/{user_id}"
    return requests.get(url, timeout=2).json()

def buscar_produto(prod_id: int):
    url = f"http://192.168.10.55:9090/products/{prod_id}"
    return requests.get(url, timeout=2).json()

try:
    u = buscar_usuario(1)
except Exception as e:
    print(f"Falha esperada (IP hardcoded): {type(e).__name__}")
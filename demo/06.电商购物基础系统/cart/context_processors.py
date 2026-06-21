"""购物车上下文处理器，将购物车对象注入所有模板上下文。"""
from .cart import Cart


def cart_processor(request):
    """向模板上下文注入购物车对象，供导航栏显示商品数量。"""
    return {'cart': Cart(request)}

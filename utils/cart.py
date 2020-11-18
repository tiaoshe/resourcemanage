from django_redis import get_redis_connection


class CartUtil(object):
    def find_cart_number(self, user_id):
        conn = get_redis_connection("default")
        cart_key = 'car_%d' % user_id
        cart_count = conn.hlen(cart_key)
        return cart_count


if __name__ == '__main__':
    num = CartUtil().find_cart_number(1)
    print(num)

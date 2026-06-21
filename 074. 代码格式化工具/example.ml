// μLang 示例：求斐波那契数列前 10 项

fn fib(n) {
    if n < 2 { return n }
    return fib(n - 1) + fib(n - 2)
}

let i = 0
while i < 10 {
    print(i, "->", fib(i))
    i = i + 1
}

// 列表与 for 循环
let xs = [10, 20, 30, 40]
let sum = 0
for i in 0..len(xs) {
    sum = sum + xs[i]
}
print("sum =", sum)

// 闭包
fn make_counter() {
    let n = 0
    fn inc() {
        n = n + 1
        return n
    }
    return inc
}
let c = make_counter()
print(c(), c(), c())

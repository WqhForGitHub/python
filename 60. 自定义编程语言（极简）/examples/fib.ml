// 计算斐波那契
fn fib(n) {
    if n < 2 {
        return n
    }
    return fib(n - 1) + fib(n - 2)
}

let i = 0
while i < 10 {
    print("fib(", i, ") =", fib(i))
    i = i + 1
}

// 简单 if/else
let x = 5
if x % 2 == 0 {
    print(x, "is even")
} else {
    print(x, "is odd")
}

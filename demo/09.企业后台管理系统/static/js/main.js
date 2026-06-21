/**
 * 企业后台管理系统 - 主脚本
 * 提供侧边栏切换等最小化交互。
 */
(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        var toggleBtn = document.getElementById("sidebarToggle");
        var sidebar = document.getElementById("sidebar");
        var mainWrapper = document.querySelector(".main-wrapper");

        if (toggleBtn && sidebar) {
            toggleBtn.addEventListener("click", function () {
                if (window.innerWidth < 992) {
                    // 移动端：显示/隐藏侧边栏
                    sidebar.classList.toggle("show");
                } else {
                    // 桌面端：折叠/展开
                    sidebar.classList.toggle("collapsed");
                    if (mainWrapper) {
                        mainWrapper.classList.toggle("expanded");
                    }
                }
            });
        }

        // 点击侧边栏外区域关闭（移动端）
        document.addEventListener("click", function (e) {
            if (window.innerWidth < 992 && sidebar && sidebar.classList.contains("show")) {
                if (!sidebar.contains(e.target) && e.target !== toggleBtn && !toggleBtn.contains(e.target)) {
                    sidebar.classList.remove("show");
                }
            }
        });

        // 自动关闭提示消息
        var alerts = document.querySelectorAll(".alert-dismissible");
        alerts.forEach(function (alert) {
            setTimeout(function () {
                var bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                if (bsAlert) {
                    bsAlert.close();
                }
            }, 4000);
        });
    });
})();

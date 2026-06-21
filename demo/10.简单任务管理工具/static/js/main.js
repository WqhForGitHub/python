/* 简单任务管理工具 - 前端交互脚本 */

document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    // 添加卡片表单的显示 / 隐藏切换
    window.toggleCardAdd = function (btn) {
        var wrapper = btn.parentElement;
        var form = wrapper.querySelector('.card-add-form');
        if (form) {
            if (form.style.display === 'none') {
                form.style.display = 'block';
                btn.style.display = 'none';
                // 聚焦到标题输入框
                var titleInput = form.querySelector('input[name="title"]');
                if (titleInput) {
                    titleInput.focus();
                }
            } else {
                form.style.display = 'none';
            }
        }
    };

    // 当卡片添加表单被取消（点击外部）时恢复按钮（简易实现）
    document.querySelectorAll('.card-add-form').forEach(function (form) {
        form.addEventListener('submit', function () {
            // 提交后保持页面跳转即可
        });
    });

    // 自动消失的提示信息（5 秒后淡出）
    setTimeout(function () {
        document.querySelectorAll('.alert').forEach(function (alert) {
            // 使用 Bootstrap 的关闭按钮，此处仅做延迟淡出
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(function () {
                if (alert.parentNode) {
                    alert.parentNode.removeChild(alert);
                }
            }, 500);
        });
    }, 5000);
});

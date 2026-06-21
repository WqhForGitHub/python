// 开发模板项目 - 主脚本
document.addEventListener('DOMContentLoaded', function() {
    console.log('开发模板项目已加载');

    // 启用所有 Bootstrap tooltip
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(el) {
        return new bootstrap.Tooltip(el);
    });
});

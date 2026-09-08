import sys
import io
sys.stdin = io.TextIOWrapper(
    sys.stdin.buffer, encoding="utf-8", errors="replace"
)
sys.stdout = io.TextIOWrapper(
    sys.stdout.buffer, encoding="utf-8", errors="replace"
)

from sales import sales_front_desk
from inventory import inventory_management
from reports import report_center
from queries import query_center


def main():
    print("=" * 50)
    print("   速驰汽车销售管理系统")
    print("=" * 50)

    while True:
        print(f"\n{'─'*50}")
        print("  主菜单")
        print(f"{'─'*50}")
        print("  1. 销售前台")
        print("  2. 库存管理")
        print("  3. 报表中心")
        print("  4. 数据查询中心（任务四 Q1-Q8）")
        print("  0. 退出系统")
        choice = input("请选择: ").strip()

        if choice == "1":
            sales_front_desk()
        elif choice == "2":
            inventory_management()
        elif choice == "3":
            report_center()
        elif choice == "4":
            query_center()
        elif choice == "0":
            print("再见！")
            break
        else:
            print("无效选项，请重新输入。")


if __name__ == "__main__":
    main()

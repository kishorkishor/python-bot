"""Simple test to verify Flet GUI loads without errors."""

import flet as ft

def main(page: ft.Page):
    page.title = "Test"
    page.add(ft.Text("If you see this, Flet works!"))

if __name__ == "__main__":
    ft.app(target=main)


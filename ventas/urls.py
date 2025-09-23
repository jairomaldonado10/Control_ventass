from django.urls import path
from . import views

app_name = "ventas"

urlpatterns = [
    # productos
    path("", views.product_list, name="product_list"),
    path("nuevo/", views.product_create, name="product_create"),
    path("<int:pk>/", views.product_detail, name="product_detail"),
    path("<int:pk>/editar/", views.product_update, name="product_update"),
    path("<int:pk>/eliminar/", views.product_delete, name="product_delete"),

    # ventas
    path("ventas/", views.venta_list, name="venta_list"),
    path("ventas/nueva/", views.venta_create, name="venta_create"),
    path("ventas/<int:pk>/", views.venta_detail, name="venta_detail"),
]

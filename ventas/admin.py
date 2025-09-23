from django.contrib import admin
from .models import Producto, Cliente, Venta, DetalleVenta

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "codigo", "precio", "stock", "actualizado")
    search_fields = ("nombre", "codigo")
    list_editable = ("precio", "stock")
    list_per_page = 20

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("rut", "nombre", "email", "actualizado")
    search_fields = ("rut", "nombre")

class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    readonly_fields = ("precio_unitario",)

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "rut_boleta", "fecha", "total")
    search_fields = ("cliente__rut", "rut_boleta")
    inlines = [DetalleVentaInline]

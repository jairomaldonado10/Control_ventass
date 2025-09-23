from django.db import models
from django.core.validators import MinValueValidator

class Producto(models.Model):
    nombre = models.CharField("Nombre", max_length=120)
    codigo = models.CharField("Código", max_length=30, unique=True)
    precio = models.DecimalField("Precio", max_digits=10, decimal_places=2,
                                 validators=[MinValueValidator(0)])
    stock = models.PositiveIntegerField("Stock", default=0)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.nombre} [{self.codigo}]"

class Cliente(models.Model):
    rut = models.CharField("RUT", max_length=12, unique=True)  # ej: 12.345.678-5
    nombre = models.CharField("Nombre", max_length=120)
    email = models.EmailField("Email", blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["rut"]

    def __str__(self):
        return f"{self.nombre} ({self.rut})"

class Venta(models.Model):
    cliente = models.ForeignKey(Cliente, null=True, blank=True, on_delete=models.SET_NULL)
    rut_boleta = models.CharField("RUT Boleta", max_length=12, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        quien = self.cliente.rut if self.cliente_id else self.rut_boleta or "sin RUT"
        return f"Venta #{self.id} - {quien}"

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.producto} x {self.cantidad}"

from decimal import Decimal

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.forms import formset_factory
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DetalleItemForm, ProductoForm, VentaHeaderForm
from .models import Cliente, DetalleVenta, Producto, Venta


# -------------------- PRODUCTOS --------------------
def product_list(request):
    """Listado con búsqueda y paginación."""
    q = request.GET.get("q", "").strip()
    qs = Producto.objects.all().order_by("id")
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(codigo__icontains=q))
    page_obj = Paginator(qs, 10).get_page(request.GET.get("page"))
    return render(request, "ventas/product_list.html", {"page_obj": page_obj, "q": q})


def product_detail(request, pk):
    obj = get_object_or_404(Producto, pk=pk)
    return render(request, "ventas/product_detail.html", {"object": obj})


def product_create(request):
    form = ProductoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        obj = form.save()
        messages.success(request, f"Producto “{obj.nombre}” creado.")
        return redirect("ventas:product_list")
    return render(
        request,
        "ventas/product_form.html",
        {"form": form, "title": "Nuevo producto"},
    )


def product_update(request, pk):
    obj = get_object_or_404(Producto, pk=pk)
    form = ProductoForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"Producto “{obj.nombre}” actualizado.")
        return redirect("ventas:product_list")
    return render(
        request,
        "ventas/product_form.html",
        {"form": form, "title": f"Editar: {obj.nombre}"},
    )


def product_delete(request, pk):
    obj = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        nombre = obj.nombre
        obj.delete()
        messages.warning(request, f"Producto “{nombre}” eliminado.")
        return redirect("ventas:product_list")
    return render(request, "ventas/product_confirm_delete.html", {"object": obj})


# -------------------- VENTAS --------------------
def venta_list(request):
    """Listado de ventas con paginación."""
    qs = Venta.objects.select_related("cliente").prefetch_related("detalles__producto")
    page_obj = Paginator(qs, 10).get_page(request.GET.get("page"))
    return render(request, "ventas/venta_list.html", {"page_obj": page_obj})


def venta_detail(request, pk):
    """Detalle de una venta con sus ítems."""
    venta = get_object_or_404(
        Venta.objects.select_related("cliente").prefetch_related("detalles__producto"),
        pk=pk,
    )
    return render(request, "ventas/venta_detail.html", {"venta": venta})


def venta_create(request):
    """
    Registra una venta:
    - Valida RUT (en el form).
    - Permite cliente habitual o solo boleta (RUT).
    - Omite filas vacías del formset (evita KeyError).
    - Valida stock por ítem.
    - Descuenta stock, crea detalles y calcula total.
    """
    ItemFormSet = formset_factory(
        DetalleItemForm, extra=2, min_num=1, validate_min=True, max_num=5
    )

    if request.method == "POST":
        header_form = VentaHeaderForm(request.POST)
        formset = ItemFormSet(request.POST, prefix="items")

        valid = header_form.is_valid() and formset.is_valid()

        # Recolectar solo filas con datos completos (producto + cantidad)
        items: list[tuple[Producto, int]] = []
        if formset.is_valid():
            for f in formset:
                cd = getattr(f, "cleaned_data", {}) or {}
                prod = cd.get("producto")
                cant = cd.get("cantidad")
                if prod and cant:
                    items.append((prod, cant))

        # Debe existir al menos un ítem válido
        if not items:
            valid = False
            messages.error(request, "Debes agregar al menos un producto con cantidad.")

        # Validar stock para cada ítem ingresado
        if valid:
            stock_ok = True
            for f in formset:
                cd = getattr(f, "cleaned_data", {}) or {}
                prod = cd.get("producto")
                cant = cd.get("cantidad")
                if prod and cant and cant > prod.stock:
                    f.add_error(
                        "cantidad",
                        f"Stock insuficiente. Disponible: {prod.stock}.",
                    )
                    stock_ok = False
            if not stock_ok:
                valid = False

        if valid:
            with transaction.atomic():
                rut = header_form.cleaned_data["rut"]

                # Cliente habitual o solo boleta
                if header_form.cleaned_data["registrar_cliente_habitual"]:
                    cliente, _ = Cliente.objects.get_or_create(
                        rut=rut,
                        defaults={
                            "nombre": header_form.cleaned_data["nombre"],
                            "email": header_form.cleaned_data.get("email") or "",
                        },
                    )
                    venta = Venta.objects.create(cliente=cliente)
                else:
                    venta = Venta.objects.create(rut_boleta=rut)

                # Crear detalles / descontar stock / calcular total
                total = Decimal("0.00")
                for prod, cant in items:
                    DetalleVenta.objects.create(
                        venta=venta,
                        producto=prod,
                        cantidad=cant,
                        precio_unitario=prod.precio,
                    )
                    prod.stock -= cant
                    prod.save(update_fields=["stock"])
                    total += prod.precio * Decimal(cant)

                venta.total = total
                venta.save(update_fields=["total"])
                messages.success(
                    request, f"Venta #{venta.id} registrada por ${venta.total}."
                )
                return redirect("ventas:venta_detail", venta.id)

        # Re-render en caso de errores
        return render(
            request, "ventas/venta_form.html", {"header_form": header_form, "formset": formset}
        )

    # GET
    header_form = VentaHeaderForm()
    formset = ItemFormSet(prefix="items")
    return render(request, "ventas/venta_form.html", {"header_form": header_form, "formset": formset})

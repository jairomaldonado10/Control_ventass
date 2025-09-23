from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import Producto
import re

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["nombre", "codigo", "precio", "stock"]
        widgets = {
            "precio": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "stock": forms.NumberInput(attrs={"min": "0"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Guardar"))

# ---- RUT helpers ----
def _normalize_rut(rut: str) -> str:
    rut = rut.strip().replace(".", "").upper()
    if "-" not in rut and len(rut) > 1:
        rut = rut[:-1] + "-" + rut[-1]
    return rut

def _rut_is_valid(rut: str) -> bool:
    rut = _normalize_rut(rut)
    if not re.match(r"^\d{1,9}-[\dK]$", rut):
        return False
    cuerpo, dv = rut.split("-")
    factores = [2, 3, 4, 5, 6, 7]
    suma = 0
    for i, dig in enumerate(reversed(cuerpo)):
        suma += int(dig) * factores[i % len(factores)]
    resto = 11 - (suma % 11)
    dv_calc = "0" if resto == 11 else "K" if resto == 10 else str(resto)
    return dv_calc == dv

class VentaHeaderForm(forms.Form):
    registrar_cliente_habitual = forms.BooleanField(required=False, label="Registrar como cliente habitual")
    rut = forms.CharField(label="RUT", max_length=12)
    nombre = forms.CharField(label="Nombre", max_length=120, required=False)
    email = forms.EmailField(label="Email", required=False)

    def clean_rut(self):
        rut = _normalize_rut(self.cleaned_data["rut"])
        if not _rut_is_valid(rut):
            raise forms.ValidationError("RUT inválido.")
        return rut

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("registrar_cliente_habitual") and not cleaned.get("nombre"):
            self.add_error("nombre", "Requerido para cliente habitual.")
        return cleaned

class DetalleItemForm(forms.Form):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all(), label="Producto", empty_label="Seleccione…"
    )
    cantidad = forms.IntegerField(label="Cantidad", min_value=1)

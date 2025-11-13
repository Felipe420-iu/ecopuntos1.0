from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Canje, MaterialTasa


class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = Usuario
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
    
class InicioSesionUsuarioForm(UserCreationForm):
    username = forms.CharField(required=True)

    class Meta:
        model = Usuario
        fields = ("username", "password")

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if not username or not password:
            raise forms.ValidationError("Ambos campos son obligatorios.")
        
        return cleaned_data

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = [
            'username', 'email', 'telefono', 'direccion', 'testimonio',
            'notificaciones_email', 'notificaciones_push', 'perfil_publico', 'mostrar_puntos',
            'foto_perfil',
        ]
        widgets = {
            'testimonio': forms.Textarea(attrs={'rows': 3}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CanjeSimpleForm(forms.ModelForm):
    """Formulario simplificado para canjes básicos sin recolección"""
    
    class Meta:
        model = Canje
        fields = ['material', 'peso', 'foto_material_inicial', 'comprobante']
        widgets = {
            'material': forms.Select(attrs={
                'class': 'form-select',
                'id': 'material_select'
            }),
            'peso': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0.1',
                'placeholder': 'Peso estimado en kg',
                'id': 'peso_input'
            }),
            'foto_material_inicial': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'comprobante': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    """Formulario integrado para solicitar canje con opción de recolección"""
    
    HORARIOS_CHOICES = [
        ('mañana', 'Mañana (8:00 AM - 12:00 PM)'),
        ('tarde', 'Tarde (12:00 PM - 6:00 PM)'),
        ('noche', 'Noche (6:00 PM - 8:00 PM)'),
        ('cualquier_hora', 'Cualquier hora'),
    ]
    
    horario_disponible = forms.ChoiceField(
        choices=HORARIOS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Canje
        fields = [
            'material', 'peso', 'foto_material_inicial', 'comprobante',
            'necesita_recoleccion', 'direccion_recoleccion', 'telefono_contacto',
            'horario_disponible', 'referencia_direccion'
        ]
        widgets = {
            'material': forms.Select(attrs={
                'class': 'form-select',
                'id': 'material_select'
            }),
            'peso': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'min': '0.1',
                'placeholder': 'Peso estimado en kg'
            }),
            'foto_material_inicial': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'comprobante': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'necesita_recoleccion': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'necesita_recoleccion'
            }),
            'direccion_recoleccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Calle 123 #45-67, Barrio Centro'
            }),
            'telefono_contacto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 300-123-4567'
            }),
            'referencia_direccion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ej: Casa color azul, al lado de la tienda, portón negro'
            })
        }
        
    def clean(self):
        cleaned_data = super().clean()
        necesita_recoleccion = cleaned_data.get('necesita_recoleccion')
        
        # Si necesita recolección, algunos campos son obligatorios
        if necesita_recoleccion:
            direccion = cleaned_data.get('direccion_recoleccion')
            telefono = cleaned_data.get('telefono_contacto')
            
            # Solo hacer obligatorio el teléfono si está marcado recolección
            if not telefono:
                raise forms.ValidationError('El teléfono es obligatorio para recolección a domicilio.')
            
            # La dirección puede ser opcional o tomarse de otro lado
            if not direccion:
                # Poner una dirección por defecto o permitir que sea opcional
                cleaned_data['direccion_recoleccion'] = 'Por confirmar por teléfono'
        
        return cleaned_data
            
        return canje
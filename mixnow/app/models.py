from django.db import models
from django.core.validators import RegexValidator
from decimal import Decimal, ROUND_DOWN

# VALIDADOR DE TELEFONO QUE TENGA EL FORMATO CORRECTO
telefono_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',  # Ejemplo: permite el formato +56912345678
    message="El número de teléfono debe tener formato: +569XXXXXXXX o 9 dígitos"
)

#-----------------------------------------------------------
#MODULO CLIENTE 

class Cliente(models.Model):
    Rut = models.CharField(max_length=12)
    cliente = models.CharField(max_length=100)
    telefono = models.CharField(validators=[telefono_validator], max_length=12, blank=True, null=True, default='')
    obra = models.CharField(max_length=50, blank=True, null=True, default='')
    persona_contacto = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.Rut} - {self.cliente}"
    
#-----------------------------------------------------------
#MODULO COTIZACIONES POR CLIENTE 

class Cotizacion(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    empresa = models.CharField(max_length=50)  # Ej: 'MixNow', 'Aridos'
    fecha = models.DateField(auto_now_add=True)
    numero_cotizacion = models.IntegerField(editable=False)
    valido_hasta = models.DateField()

    def save(self, *args, **kwargs):
        if not self.pk:
            # Buscar la última cotización solo para esta empresa
            ultima = Cotizacion.objects.filter(empresa=self.empresa).order_by('-numero_cotizacion').first()
            if ultima:
                self.numero_cotizacion = ultima.numero_cotizacion + 1
            else:
                self.numero_cotizacion = 3000  # Cada empresa empieza desde 3000
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Cotización {self.numero_cotizacion} - {self.cliente} ({self.empresa})"

#CALCULOS TOTALES POR COTIZACION 

    IVA = 0.19  # 19%

    def subtotal_general(self):
        return sum(item.subtotal() for item in self.items.all())

    def iva_total(self):
        return self.subtotal_general() * self.IVA

    def total_general(self):
        return self.subtotal_general() + self.iva_total()

#-----------------------------------------------------------

class Item(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items')
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, null=True, blank=True) 
    cantidad_m3 = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.CharField(max_length=100, blank=False, null=False)

    MONEDAS = (
        ('CLP', 'CLP'),
        ('UF', 'UF'),
    )
    moneda = models.CharField(max_length=3, choices=MONEDAS, default='CLP')

    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    IVA = 0.19  # 19%

    #SUBTOTAL POR ITEM
    def subtotal(self):
        return float(self.cantidad_m3) * float(self.precio_unitario)

    #IVA POR ITEM
    def iva(self):
        return self.subtotal() * self.IVA

    #TOTAL DE CADA ITEM
    def total(self):    
        return self.subtotal() + self.iva()


    def __str__(self):
        return f"{self.descripcion} ({self.cotizacion.cliente})"

#-----------------------------------------------------------
#MODULO DE CAMIONES

class Camiones(models.Model):
    empresa = models.CharField(max_length=100)
    vehiculo = models.CharField(max_length=100)
    patente = models.CharField(max_length=20, unique=True)
    descripcion = models.TextField(blank=True)
    revision_tecnica = models.DateField()
    circulacion = models.DateField()
    seguro = models.DateField()

    def __str__(self):
        return f"{self.vehiculo} - {self.patente}"

class Documento(models.Model):
    camion = models.ForeignKey(Camiones, on_delete=models.CASCADE, related_name='documentos')
    titulo = models.CharField(max_length=100)
    archivo = models.FileField(upload_to='pdfs/')

    def __str__(self):
        return self.titulo

class Empresas(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre
    
#-----------------------------------------------------------
#MODULO TRABAJADORES

class Trabajadores(models.Model):
    nombre = models.CharField(max_length=100)
    empresa = models.ForeignKey(Empresas, on_delete=models.CASCADE, related_name='trabajadores')

    def __str__(self):
        return self.nombre


class DocumentoTrabajador(models.Model):
    trabajador = models.ForeignKey(Trabajadores, on_delete=models.CASCADE, related_name='documentos')
    titulo = models.CharField(max_length=100)
    archivo = models.FileField(upload_to='pdfs/')

    def __str__(self):
        return self.titulo

#------------------------------------------------------------
#MODULO DE ESTADOS DE PAGO

class EstadosdePago(models.Model):
    fecha_emision = models.DateField()
    mes_servicio = models.CharField(max_length=20)
    tipo_servicio = models.CharField(max_length=50)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, null=True, blank=True)
    usar_uf = models.BooleanField(default=False)
    valor_uf = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:  # Si es un nuevo registro
            ultimo = EstadosdePago.objects.order_by('-id').first()
            if ultimo:
                if ultimo.id < 400:
                    self.pk = 400
                else:
                    self.pk = ultimo.id + 1
            else:
                self.pk = 400  # Si no hay registros, empezar desde 400
        super().save(*args, **kwargs)

    def __str__(self):
        return self.tipo_servicio
    
    IVA = Decimal('0.19') 
    
    #VALOR EN TOTAL SUMA DE TODOS LOS ITEMS AGREGADOS AL EPP
    def total_neto_edp(self):
        # Suma de los valores netos por item (ya en CLP o en UF según item)
        total = sum(item.valor_neto_por_item() for item in self.items.all())
        # Aseguramos trabajar con Decimal
        total = Decimal(str(total))

        if self.usar_uf and self.valor_uf:
            # Si el estado está marcado para usar UF, los valores de los items
            # se guardaron en UF y hay que convertir a CLP usando el valor guardado
            clp_total = total * Decimal(str(self.valor_uf))
            # Eliminar los centavos (redondear hacia abajo a pesos enteros)
            return clp_total.quantize(Decimal('1'), rounding=ROUND_DOWN)

        # Si no se usa UF, truncamos los centavos del total neto en CLP
        return total.quantize(Decimal('1'), rounding=ROUND_DOWN)

    #IVA TOTAL DE TODOS LOS ITEMS
    def total_con_iva_edp(self):
        # Calcular IVA sobre el neto ya truncado y devolver en pesos enteros
        iva = Decimal(str(self.total_neto_edp())) * self.IVA
        return iva.quantize(Decimal('1'), rounding=ROUND_DOWN)
    
    #VALOR TOTAL DE TODOS LOS ITEMS CON IVA INCLUIDO
    def total_general_edp(self):
        total = Decimal(str(self.total_neto_edp())) + Decimal(str(self.total_con_iva_edp()))
        return total.quantize(Decimal('1'), rounding=ROUND_DOWN)
    
    #VALOR EN UF (si corresponde)
    def total_en_uf(self):
        if self.usar_uf and self.valor_uf:
            return self.total_neto_edp() / Decimal(str(self.valor_uf))
        return None

class Itemepp(models.Model):
    estados_de_pago = models.ForeignKey(EstadosdePago, on_delete=models.CASCADE, related_name='items')
    guia = models.IntegerField()
    fecha_item = models.DateField()
    material = models.CharField(max_length=50)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    patente = models.CharField(max_length=20)
    unidad = models.CharField(max_length=10)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.material
    
    #VALOR NETO DE CADA ITEM 
    def valor_neto_por_item(self):
        # Calcular valor neto y truncar los centavos (no considerar los decimales)
        total = Decimal(str(self.precio_unitario)) * Decimal(str(self.cantidad))
        return total.quantize(Decimal('1'), rounding=ROUND_DOWN)

    def valor_neto_clp(self):
        """Devuelve el valor neto del item en CLP.
        Si el estado usa UF y tiene valor_uf, interpreta `precio_unitario` como UF
        y convierte a CLP: precio_unitario * cantidad * valor_uf.
        En caso contrario, devuelve el neto ya en CLP.
        """
        total = Decimal(str(self.precio_unitario)) * Decimal(str(self.cantidad))
        if self.estados_de_pago and self.estados_de_pago.usar_uf and self.estados_de_pago.valor_uf:
            clp = total * Decimal(str(self.estados_de_pago.valor_uf))
            return clp.quantize(Decimal('1'), rounding=ROUND_DOWN)
        return total.quantize(Decimal('1'), rounding=ROUND_DOWN)
    
    #VALOR EN UF DE CADA ITEM
    def valor_en_uf(self):
        # Si el estado está en UF, precio_unitario ya está en UF
        if self.estados_de_pago and self.estados_de_pago.usar_uf:
            return Decimal(str(self.precio_unitario))
        # Si el precio está en CLP y hay valor_uf, convertir a UF
        if self.estados_de_pago and self.estados_de_pago.valor_uf:
            return (Decimal(str(self.precio_unitario)) / Decimal(str(self.estados_de_pago.valor_uf)))
        return None
    
    #VALOR TOTAL EN UF
    def total_en_uf(self):
        # Devuelve el total del item en UF
        if self.estados_de_pago and self.estados_de_pago.usar_uf:
            return (Decimal(str(self.precio_unitario)) * Decimal(str(self.cantidad)))
        if self.estados_de_pago and self.estados_de_pago.valor_uf:
            total_clp = Decimal(str(self.precio_unitario)) * Decimal(str(self.cantidad))
            return total_clp / Decimal(str(self.estados_de_pago.valor_uf))
        return None
#------------------------------------------------------------
    
    




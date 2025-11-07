from django.urls import reverse, reverse_lazy
from django.views.generic.list import ListView 
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.detail import DetailView
from django.shortcuts import redirect, render , get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import ClienteForm, ItemForm , CamionesForm ,TrabajadoresForm , ItemeppForm , EstadosdePagoForm
from .models import Cliente, Item, Cotizacion , Camiones , Documento , Empresas , Trabajadores , DocumentoTrabajador , EstadosdePago , Itemepp
from django.http import HttpResponseRedirect
from django.contrib import messages
import os
from django.utils import timezone
import requests
from django.http import JsonResponse
from django.core.cache import cache


@user_passes_test(lambda u: u.is_superuser)
def inicio(request):
    return render(request, 'clientes/inicio.html')


@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class Listar_Clientes(LoginRequiredMixin, UserPassesTestMixin, ListView):
    def test_func(self):
        return self.request.user.is_superuser
    model = Cliente
    template_name = "clientes/listar_clientes.html"
    context_object_name = 'clientes'


@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class Crear_Cliente(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    def test_func(self):
        return self.request.user.is_superuser
    model = Cliente
    form_class = ClienteForm
    template_name = "clientes/crear_cliente.html"
    success_url = reverse_lazy('listar_clientes')


@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class Editar_Cliente(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    def test_func(self):
        return self.request.user.is_superuser
    model = Cliente
    form_class = ClienteForm
    template_name = "clientes/editar_cliente.html"
    success_url = reverse_lazy('listar_clientes')


@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class Eliminar_Cliente(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    def test_func(self):
        return self.request.user.is_superuser
    model = Cliente
    template_name = "clientes/eliminar_cliente.html"
    success_url = reverse_lazy('listar_clientes')

# ======================================
# VISTA DETALLE CLIENTE - AGREGAR ITEMS
# ======================================
@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class Detalle_Clientes(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Cliente
    template_name = "clientes/detalle_cliente.html"
    context_object_name = 'cliente'
    form_class = ItemForm

    def test_func(self):
        # Permite solo superusuarios
        return self.request.user.is_superuser

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        accion = request.POST.get('accion')

        # Inicializamos la sesión si no existe
        if 'items_temporales' not in request.session:
            request.session['items_temporales'] = []

        # -----------------------------
        # Agregar item temporal
        # -----------------------------
        if accion == 'agregar_item':
            form = ItemForm(request.POST)
            if form.is_valid():
                item_data = {
                    'cantidad_m3': float(form.cleaned_data['cantidad_m3']),
                    'descripcion': form.cleaned_data['descripcion'],
                    'moneda': form.cleaned_data['moneda'],
                    'precio_unitario': float(form.cleaned_data['precio_unitario']),
                }
                # Guardamos el item en la sesión
                request.session['items_temporales'].append(item_data)
                request.session.modified = True
            return redirect('detalle_cliente', pk=self.object.pk)

        # -----------------------------
        # Eliminar item temporal
        # -----------------------------
        elif accion == 'eliminar_item':
            index = int(request.POST.get('item_index'))
            if 0 <= index < len(request.session['items_temporales']):
                request.session['items_temporales'].pop(index)
                request.session.modified = True
            return redirect('detalle_cliente', pk=self.object.pk)

        # -----------------------------
        # Crear cotización
        # -----------------------------
        elif accion == 'crear_cotizacion':
            # Llamamos a la función que maneja la creación de la cotización
            return self.crear_cotizacion(request)

        # Si no es ninguna acción, redirigimos al detalle
        return redirect('detalle_cliente', pk=self.object.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pasamos el formulario y los items temporales a la plantilla
        context['form'] = ItemForm()
        context['items_temporales'] = self.request.session.get('items_temporales', [])
        return context

    # ==============================
    # FUNCION PARA CREAR COTIZACION
    # ==============================
    def crear_cotizacion(self, request):
        """
        Método para crear una cotización a partir de los ítems temporales almacenados en la sesión.
        Se ejecuta cuando el usuario presiona el botón 'Crear Cotización'.
        """

        # Obtenemos los datos enviados por POST desde el formulario de crear cotización
        opcion_destino = request.POST.get('opcion_destino')  # Empresa seleccionada
        valido_hasta = request.POST.get('valido_hasta')      # Fecha de validez

        # Validamos que haya al menos un ítem agregado
        if not request.session.get('items_temporales'):
            messages.error(request, "Debes agregar al menos un ítem antes de crear la cotización.")
            return redirect('detalle_cliente', pk=self.object.pk)

        # Creamos la cotización en la base de datos
        cotizacion = Cotizacion.objects.create(
            cliente=self.object,
            empresa=opcion_destino.capitalize(),
            valido_hasta=valido_hasta
        )

        # Creamos los ítems asociados a la cotización
        for i in request.session['items_temporales']:
            Item.objects.create(
                cotizacion=cotizacion,
                cantidad_m3=i['cantidad_m3'],
                descripcion=i['descripcion'],
                moneda=i['moneda'],
                precio_unitario=i['precio_unitario']
            )

        # Limpiamos los ítems de la sesión ya que fueron creados en DB
        request.session['items_temporales'] = []
        request.session.modified = True

        # Redirigimos según la empresa seleccionada
        rutas = {
            "aridos": 'vista_aridos',
            "valentino": 'vista_valentino',
            "inverland": 'vista_inverland',
            "mixnow": 'vista_mixnow',
            "mixnow_antofagasta":"vista_mixnow_antofagasta"
        }
        return HttpResponseRedirect(reverse(rutas[opcion_destino], kwargs={'cotizacion_id': cotizacion.id}))

# PLANTILLAS DE LAS 4 EMPRESAS DIFERENTES

# Aridos
@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class CotizacionAridosView(DetailView):
    model = Cotizacion
    template_name = "clientes/aridos.html"
    context_object_name = "cotizacion"

    def get_object(self):
        cotizacion_id = self.kwargs.get('cotizacion_id')
        return Cotizacion.objects.get(id=cotizacion_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['cliente'] = self.object.cliente
        return context

# Valentino
@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class CotizacionValentinoView(DetailView):
    model = Cotizacion
    template_name = "clientes/valentino.html"
    context_object_name = "cotizacion"

    def get_object(self):
        cotizacion_id = self.kwargs.get('cotizacion_id')
        return Cotizacion.objects.get(id=cotizacion_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['cliente'] = self.object.cliente
        return context

# Inverland
@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class CotizacionInverlandView(DetailView):
    model = Cotizacion
    template_name = "clientes/inverland.html"
    context_object_name = "cotizacion"

    def get_object(self):
        cotizacion_id = self.kwargs.get('cotizacion_id')
        return Cotizacion.objects.get(id=cotizacion_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['cliente'] = self.object.cliente
        return context

# MixNowArica
class CotizacionMixNowView(DetailView):
    model = Cotizacion
    template_name = "clientes/mixnow.html"
    context_object_name = "cotizacion"

    def get_object(self):
        cotizacion_id = self.kwargs.get('cotizacion_id')
        return Cotizacion.objects.get(id=cotizacion_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['cliente'] = self.object.cliente
        return context

#MixNowAntofagasta
class CotizacionMixNowAntofagastaView(DetailView):
    model = Cotizacion
    template_name = "clientes/mixnow_antofagasta.html"
    context_object_name = "cotizacion"

    def get_object(self):
        cotizacion_id = self.kwargs.get('cotizacion_id')
        return Cotizacion.objects.get(id=cotizacion_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['cliente'] = self.object.cliente
        return context


from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML, CSS


def descargar_pdf(request, cotizacion_id, plantilla):
    cotizacion = Cotizacion.objects.get(id=cotizacion_id)
    items = cotizacion.items.all()
    cliente = cotizacion.cliente

    html_string = render_to_string(f'clientes/{plantilla}.html', {
        'cliente': cliente,
        'cotizacion': cotizacion,
        'items': items
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cotizacion_{cotizacion.id}.pdf"'

    # AQUI SE APLICA EL TAMAÑO A4 AL PDF PARA OCUPAR MAS ESPACIO DE LA HOJA 
    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(
        response,
        stylesheets=[
            CSS(string='''
                @page {
                    size: A4;
                    margin-top: -1.3cm; 
                    margin-left: 0cm;
                    margin-right: 0cm;
                    margin-bottom: 0cm;
                }
            ''')
        ]
    )

    return response


#INSTRUCCIONES 
@user_passes_test(lambda u: u.is_superuser)
def instrucciones(request):
    return render(request, 'clientes/instrucciones.html')


# CRUD Camiones
@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class Listar_Camiones(ListView):
    model = Camiones
    template_name = "clientes/listar_camiones.html"
    context_object_name = "camiones"

@user_passes_test(lambda u: u.is_superuser)
def crear_camion(request):
    if request.method == 'POST':
        form = CamionesForm(request.POST, request.FILES)
        if form.is_valid():
            camion = form.save()

            # Guardar varios archivos
            archivos = request.FILES.getlist('archivos')
            for archivo in archivos:
                Documento.objects.create(
                    camion=camion,
                    titulo=archivo.name,
                    archivo=archivo
                )

            return redirect('listar_camiones')  
    else:
        form = CamionesForm()

    return render(request, 'clientes/crear_camion.html', {'form': form})


@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class Eliminar_Camion(DeleteView):
    model = Camiones
    template_name = "clientes/eliminar_camion.html"
    success_url = reverse_lazy('listar_camiones')


@user_passes_test(lambda u: u.is_superuser)
def documentos_camion(request, camion_id):
    camion = Camiones.objects.get(id=camion_id)
    documentos = camion.documentos.all()
    return render(request, 'clientes/documentos_camion.html', {
        'camion': camion,
        'documentos': documentos
    })


@user_passes_test(lambda u: u.is_superuser)
def Actualizar_Camion(request, pk):
    camion = get_object_or_404(Camiones, pk=pk)

    if request.method == 'POST':
        form = CamionesForm(request.POST, request.FILES, instance=camion)
        if form.is_valid():
            camion = form.save()

            # Guardar nuevos archivos si se suben
            archivos = request.FILES.getlist('archivos')
            for archivo in archivos:
                Documento.objects.create(
                    camion=camion,
                    titulo=archivo.name,
                    archivo=archivo
                )

            messages.success(request, "Camión actualizado correctamente.")
            return redirect('listar_camiones')
        else:
            print(form.errors)  
    else:
        form = CamionesForm(instance=camion)

    # Aseguramos que las fechas salgan correctamente formateadas
    if camion.revision_tecnica:
        form.initial['revision_tecnica'] = camion.revision_tecnica.strftime('%Y-%m-%d')
    if camion.circulacion:
        form.initial['circulacion'] = camion.circulacion.strftime('%Y-%m-%d')
    if camion.seguro:
        form.initial['seguro'] = camion.seguro.strftime('%Y-%m-%d')

    return render(request, 'clientes/editar_camion.html', {
        'form': form,
        'camion': camion
    })

@user_passes_test(lambda u: u.is_superuser)
def eliminar_documento(request, doc_id):
    documento = get_object_or_404(Documento, id=doc_id)
    camion_id = documento.camion.id  # Para redirigir después de eliminar

    # Borrar archivo físico si existe
    if documento.archivo and os.path.isfile(documento.archivo.path):
        os.remove(documento.archivo.path)

    # Borrar el objeto de la base de datos
    documento.delete()

    return redirect('documentos_camion', camion_id=camion_id)


@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class Vencimiento_fechas_camiones(ListView):
    model = Camiones
    template_name = "clientes/fechas_camiones.html"
    context_object_name = "camiones"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from datetime import date
        from dateutil.relativedelta import relativedelta  

        hoy = date.today()
        camiones_con_fechas = []

        for camion in context['camiones']:
            # Calcular diferencia exacta en meses y días
            def calcular_estado(fecha):
                if fecha < hoy:
                    return 'VENCIDO', 'danger'
                else:
                    diff = relativedelta(fecha, hoy)
                    meses = diff.months + diff.years * 12
                    dias = diff.days
                    texto = ""
                    if meses > 0:
                        texto += f"{meses} mes{'es' if meses > 1 else ''}"
                    if dias > 0:
                        if texto:
                            texto += " y "
                        texto += f"{dias} día{'s' if dias > 1 else ''}"
                    return f"Faltan {texto}", 'success'

            camion_info = {
                'vehiculo': camion.vehiculo,
                'patente': camion.patente,
                'empresa': camion.empresa,
                'documentos': [
                    {
                        'nombre': 'Revisión Técnica',
                        'estado': calcular_estado(camion.revision_tecnica)[0],
                        'clase': calcular_estado(camion.revision_tecnica)[1]
                    },
                    {
                        'nombre': 'Permiso Circulación',
                        'estado': calcular_estado(camion.circulacion)[0],
                        'clase': calcular_estado(camion.circulacion)[1]
                    },
                    {
                        'nombre': 'Seguro',
                        'estado': calcular_estado(camion.seguro)[0],
                        'clase': calcular_estado(camion.seguro)[1]
                    }
                ]
            }
            camiones_con_fechas.append(camion_info)

        context['camiones_con_fechas'] = camiones_con_fechas
        return context


@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class Listar_Empresa(LoginRequiredMixin, UserPassesTestMixin, ListView):
    def test_func(self):
        return self.request.user.is_superuser
    model = Empresas
    template_name = "clientes/listar_empresa.html"
    context_object_name = 'empresa'


def crear_Trabajador(request):
    empresa = None  # por defecto
    # si vienes desde una empresa específica:
    empresa_id = request.GET.get('empresa_id')  # o como lo pases
    if empresa_id:
        empresa = get_object_or_404(Empresas, pk=empresa_id)

    if request.method == 'POST':
        form = TrabajadoresForm(request.POST, request.FILES)
        if form.is_valid():
            trabajador = form.save(commit=False)
            if empresa:
                trabajador.empresa = empresa
            trabajador.save()

            archivos = request.FILES.getlist('archivos')
            for archivo in archivos:
                DocumentoTrabajador.objects.create(
                    trabajador=trabajador,
                    titulo=archivo.name,
                    archivo=archivo
                )
            if empresa:
                return redirect('listar_trabajadores', empresa.id)
            return redirect('listar_empresas')
    else:
        form = TrabajadoresForm()
    return render(request, 'clientes/crear_trabajador.html', {'form': form, 'empresa': empresa})

@user_passes_test(lambda u: u.is_superuser)
def Actualizar_Trabajadores(request, pk):
    trabajador = get_object_or_404(Trabajadores, pk=pk)

    if request.method == 'POST':
        form = TrabajadoresForm(request.POST, request.FILES, instance=trabajador)
        if form.is_valid():
            trabajador = form.save()

            # Guardar nuevos archivos si se suben
            archivos = request.FILES.getlist('archivos')
            for archivo in archivos:
                DocumentoTrabajador.objects.create(
                    trabajador=trabajador,
                    titulo=archivo.name,
                    archivo=archivo
                )

            messages.success(request, "Trabajador actualizado correctamente.")
            return redirect('listar_trabajadores', empresa_id=trabajador.empresa.id)
        else:
            print(form.errors)
    else:
        form = TrabajadoresForm(instance=trabajador)

    documentos = DocumentoTrabajador.objects.filter(trabajador=trabajador)

    return render(request, 'clientes/editar_trabajadores.html', {
        'form': form,
        'trabajador': trabajador,
        'documentos': documentos
    })


@user_passes_test(lambda u: u.is_superuser)
def eliminar_documento_trabajador(request, doc_id):
    documento = get_object_or_404(DocumentoTrabajador, id=doc_id)
    empresa_id = documento.trabajador.empresa.id  # obtener la empresa del trabajador

    # Borrar archivo físico si existe
    if documento.archivo and os.path.isfile(documento.archivo.path):
        os.remove(documento.archivo.path)

    documento.delete()
    # Redirige a la lista de trabajadores de esa empresa
    return redirect('listar_trabajadores', empresa_id=empresa_id)

@user_passes_test(lambda u: u.is_superuser)
def Eliminar_Trabajadores(request, pk):
    trabajador = get_object_or_404(Trabajadores, pk=pk)
    empresa_id = trabajador.empresa.id

    if request.method == "POST":
        # El usuario confirmó la eliminación
        trabajador.delete()
        return redirect('listar_trabajadores', empresa_id=empresa_id)

    # Si es GET, mostramos la página de confirmación
    return render(request, 'clientes/eliminar_trabajadores.html', {'trabajador': trabajador})


@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class Listar_Trabajadores(ListView):
    model = Trabajadores
    template_name = "clientes/listar_trabajadores.html"
    context_object_name = "trabajadores"

    def get_queryset(self):
        empresa_id = self.kwargs['empresa_id']
        return Trabajadores.objects.filter(empresa_id=empresa_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa_id = self.kwargs['empresa_id']
        context['empresa'] = Empresas.objects.get(id=empresa_id)
        return context


@user_passes_test(lambda u: u.is_superuser)
def documento_trabajador(request, trabajador_id):
    trabajador = Trabajadores.objects.get(id=trabajador_id)
    documentos = trabajador.documentos.all()
    return render(request, 'clientes/documentos_trabajador.html', {
        'trabajador': trabajador,
        'documentos': documentos
    })

@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class Detalle_Cliente_EDP(DetailView):
    model = Cliente
    template_name = "clientes/detalle_cliente_epp.html"
    context_object_name = 'cliente'

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Capturamos las acciones según tu HTML
        accion_edp = request.POST.get('accion_edp')
        accion_crear_edp = request.POST.get('accion_crear_edp')
        accion_eliminar = request.POST.get('accion_eliminar')

        # Inicializar sesión
        if 'items_temporales_epp' not in request.session:
            request.session['items_temporales_epp'] = []

        # Inicializar variable de tipo de precio (UF o normal)
        if 'usar_uf' not in request.session:
            request.session['usar_uf'] = False

        # ===== Agregar ítem temporal =====
        if accion_edp == 'agregar_item_edp':
            form = ItemeppForm(request.POST)
            if form.is_valid():
                item_data = {
                    'fecha_item': str(form.cleaned_data['fecha_item']),
                    'guia': form.cleaned_data['guia'],
                    'material': form.cleaned_data['material'],
                    'cantidad': float(form.cleaned_data['cantidad']),
                    'patente': form.cleaned_data['patente'],
                    'unidad': form.cleaned_data['unidad'],
                    'precio_unitario': float(form.cleaned_data['precio_unitario']),
                }
                request.session['items_temporales_epp'].append(item_data)
                request.session.modified = True
            return redirect('detalle_cliente_epp', pk=self.object.pk)

        # ===== Eliminar ítem temporal =====
        elif accion_eliminar == 'eliminar_item':
            index = int(request.POST.get('itemindex'))
            if 0 <= index < len(request.session['items_temporales_epp']):
                request.session['items_temporales_epp'].pop(index)
                request.session.modified = True
            return redirect('detalle_cliente_epp', pk=self.object.pk)

        # ===== Crear estado de pago =====
        elif accion_crear_edp == 'crear_estado_de_pago':
            # Guardar la preferencia de UF en la sesión
            usar_uf = request.POST.get('usar_uf') == 'true'
            request.session['usar_uf'] = usar_uf
            request.session.modified = True
            return self.crear_estado(request)
            
        # Si no coincide ninguna acción, redirige al detalle
        return redirect('detalle_cliente_epp', pk=self.object.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ItemeppForm()
        context['estado_form'] = EstadosdePagoForm()
        context['items_temporales'] = self.request.session.get('items_temporales_epp', [])
        
        # Si estamos usando UF, usamos el valor cacheado (24h) para calcular UF
        usar_uf = self.request.session.get('usar_uf', False)
        if usar_uf:
            valor_uf = cache.get('valor_uf')
            if valor_uf:
                items_con_uf = []
                for item in context['items_temporales']:
                    item_copy = item.copy()
                    precio = float(item['precio_unitario'])
                    cantidad = float(item.get('cantidad', item.get('cantidad_m3', 0)))
                    try:
                        # En modo UF, el precio ingresado es en UF
                        item_copy['valor_uf'] = precio  # Mantener el precio en UF como se ingresó
                        # El valor neto en CLP ya viene calculado
                        item_copy['valor_neto_clp'] = item.get('valor_neto_clp', int(precio * cantidad * float(valor_uf)))
                    except Exception as e:
                        print(f"Error al procesar item: {e}")
                        item_copy['valor_uf'] = None
                        item_copy['valor_neto_clp'] = 0
                    items_con_uf.append(item_copy)
                context['items_temporales'] = items_con_uf
                context['valor_uf_actual'] = valor_uf
            else:
                # Si no hay valor en cache, no hacemos la llamada aquí para evitar demoras
                context['valor_uf_actual'] = None

        context['usar_uf'] = usar_uf
        return context

    def crear_estado(self, request):
        if not request.session.get('items_temporales_epp'):
            return redirect('detalle_cliente_epp', pk=self.object.pk)

        form = EstadosdePagoForm(request.POST)
        if form.is_valid():
            estado = form.save(commit=False)
            estado.cliente = self.object
            
            # Obtener la opción de UF
            usar_uf = request.POST.get('usar_uf') == 'true'
            estado.usar_uf = usar_uf
            
            # Si se usa UF, obtener y guardar el valor actual (petición única)
            if usar_uf:
                try:
                    response = requests.get("https://mindicador.cl/api/uf", timeout=8)
                    data = response.json()
                    valor_uf = data['serie'][0]['valor']
                    estado.valor_uf = valor_uf
                    # cachear por 24 horas (86400 segundos)
                    try:
                        cache.set('valor_uf', valor_uf, 86400)
                    except Exception:
                        pass
                except Exception as e:
                    print(f"Error al obtener UF: {str(e)}")
                    estado.valor_uf = None
                    # eliminar cache si existe para forzar futura recarga
                    try:
                        cache.delete('valor_uf')
                    except Exception:
                        pass
            else:
                # Si no se usa UF, eliminar valor en cache para evitar uso accidental
                try:
                    cache.delete('valor_uf')
                except Exception:
                    pass
            
            estado.save()

            # Crear los ítems asociados desde la sesión
            for i in request.session['items_temporales_epp']:
                precio_unitario = float(i['precio_unitario'])
                Itemepp.objects.create(
                    estados_de_pago=estado,
                    fecha_item=i['fecha_item'],
                    guia=i['guia'],
                    material=i['material'],
                    cantidad=i['cantidad'],
                    patente=i['patente'],
                    unidad=i['unidad'],
                    precio_unitario=precio_unitario
                )

            # Limpiar sesión
            request.session['items_temporales_epp'] = []
            request.session.modified = True

            # Redirigir según empresa seleccionada
            opcion_destino_edp = request.POST.get('opcion_destino_edp')
            rutas = {
                "empresa_aridos": "estado_pago_aridos",
                "empresa_valentino": "estado_pago_valentino",
                "empresa_inverland": "estado_pago_inverland",
                "empresa_mixnow": "estado_pago_mixnow"
            }
            if opcion_destino_edp in rutas:
                return redirect(rutas[opcion_destino_edp], estado_id=estado.id)

        # Si el formulario no es válido, renderizar con errores
        context = self.get_context_data()
        context['estado_form'] = form
        return self.render_to_response(context)
    
@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class EstadoPagoMixNowView(DetailView):
    model = EstadosdePago
    template_name = "clientes/estado_pago_mixnow.html"
    context_object_name = "estado"

    def get_object(self):
        estado_id = self.kwargs.get('estado_id')
        return EstadosdePago.objects.get(id=estado_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['total_neto_edp'] = self.object.total_neto_edp()
        context['total_con_iva_edp'] = self.object.total_con_iva_edp()
        context['total_general_edp'] = self.object.total_general_edp()

        context['cliente'] = self.object.cliente
        return context
    
@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class EstadoPagoAridosView(DetailView):
    model = EstadosdePago
    template_name = "clientes/estado_pago_aridos.html"
    context_object_name = "estado"

    def get_object(self):
        estado_id = self.kwargs.get('estado_id')
        return EstadosdePago.objects.get(id=estado_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['total_neto_edp'] = self.object.total_neto_edp()
        context['total_con_iva_edp'] = self.object.total_con_iva_edp()
        context['total_general_edp'] = self.object.total_general_edp()
        
        context['cliente'] = self.object.cliente
        return context

@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class EstadoInverlandView(DetailView):
    model = EstadosdePago
    template_name = "clientes/estado_pago_inverland.html"
    context_object_name = "estado"

    def get_object(self):
        estado_id = self.kwargs.get('estado_id')
        return EstadosdePago.objects.get(id=estado_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['total_neto_edp'] = self.object.total_neto_edp()
        context['total_con_iva_edp'] = self.object.total_con_iva_edp()
        context['total_general_edp'] = self.object.total_general_edp()

        context['cliente'] = self.object.cliente
        return context
    
@method_decorator(user_passes_test(lambda u: u.is_superuser), name='dispatch')
class EstadoPagoValentinoView(DetailView):
    model = EstadosdePago
    template_name = "clientes/estado_pago_valentino.html"
    context_object_name = "estado"

    def get_object(self):
        estado_id = self.kwargs.get('estado_id')
        return EstadosdePago.objects.get(id=estado_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = self.object.items.all()
        context['total_neto_edp'] = self.object.total_neto_edp()
        context['total_con_iva_edp'] = self.object.total_con_iva_edp()
        context['total_general_edp'] = self.object.total_general_edp()

        context['cliente'] = self.object.cliente
        return context
    
def descargar_pdf_edp(request, estado_id, plantilla):
    estado = EstadosdePago.objects.get(id=estado_id)
    items = estado.items.all()  
    cliente = estado.cliente

    html_string = render_to_string(f'clientes/{plantilla}.html', {
        'estado': estado,
        'items': items,
        'cliente': cliente,
        'total_neto_edp': estado.total_neto_edp(),
        'total_con_iva_edp': estado.total_con_iva_edp(),
        'total_general_edp': estado.total_general_edp(),
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="estado_pago_{estado.id}.pdf"'

    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(
        response,
        stylesheets=[CSS(string='''
            @page {
                size: A4;
                margin-top: 0cm; 
                margin-left: 0cm;
                margin-right: 0cm;
                margin-bottom: 0cm;
            }
        ''')]
    )

    return response


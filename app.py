from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired
from alternativas import * 
from funciones import *
import pandas as pd
import numpy_financial as npf
import json 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
bootstrap = Bootstrap(app)

class MyForm(FlaskForm):
    dni = StringField('DNI:')
    tasa_particular = SelectField('Tasa particular:', choices=[("0", "NO"), ("1", "SI")])
    comision_particular = SelectField('Comisión particular:', choices=[("0", "NO"), ("1", "SI")])
    num_propiedad = IntegerField('N° propiedades:')
    tasa = StringField('Tasa:')
    comision = StringField('Comisión:')
    comision01 = StringField('Comisión:')
    tasa10 = StringField('Tasa:')
    cuota_mixta = StringField('Cuota mixta:')
    monto = StringField('Monto:')
    monto_unidad = SelectField('Moneda:', choices=monto_unidades)
    esquema = SelectField('Esquema:', choices=esquemas)
    #pago_puntual = SelectField('¿Pago puntual?:', choices=pagos_puntuales)
    compra_venta = SelectField('¿Operación compra venta?:', choices=compras_ventas)
    con_hipoteca = SelectField('¿Con hipoteca?:', choices=con_hipotecas)
    opcion_broker = SelectField('¿Tiene Broker?:', choices=opciones_brokers)
    tipo_pagador = SelectField('¿Tipo pagador?:', choices=tipo_pagadores)

    plazo = StringField('Plazo(meses):')

    submit = SubmitField('Generar Cronograma')


nro_operacion = 1
@app.route('/', methods=['GET', 'POST'])
def index():
    global nro_operacion  # Declaración de la variable como global
    form = MyForm()
    if form.validate_on_submit():
        dni = form.dni.data
        numPropiedades = int(form.num_propiedad.data)
        tasa_particular = form.tasa_particular.data
        comision_particular = form.comision_particular.data
        if form.tasa_particular.data == '1':
            tasa_particular = form.tasa10.data
            
        if form.comision_particular.data == '1':
            comision_particular = form.comision01.data
            
        if form.tasa_particular.data == '1' and form.comision_particular.data == '1':
            tasa_particular = form.tasa.data
            comision_particular = form.comision.data
       
        
        # Obtener valores de los campos de distrito y tipo de propiedad utilizando sus IDs
        lista_distritos = []
        lista_tipos_propiedades = []
        lista_niveles_riesgos = []
        lista_tipos_deudas = []
        try:
            for i in range(numPropiedades):
                distritos = request.form.getlist(f'inputDistrito{i}')[0]
                tipos_propiedad = request.form.getlist(f'inputTipoPropiedad{i}')[0]
                nivel_riesgo = request.form.getlist(f'inputNivelRiesgo{i}')[0]
                tipo_deuda = "Medio con castigo vigente"
                lista_distritos.append(distritos)
                lista_tipos_propiedades.append(tipos_propiedad)
                lista_niveles_riesgos.append(nivel_riesgo)
                lista_tipos_deudas.append(tipo_deuda)
        except: 
            pass

        tasa_particular = tasa_particular
        comision_particular = comision_particular
        nro_propiedades = numPropiedades
        monto = form.monto.data
        monto_unidad = numeroATexto_MontoUnidades(form.monto_unidad.data)
        esquema = numeroATexto_Esquema(form.esquema.data)
        #pago_puntual = numeroATexto_PagoPuntual(form.pago_puntual.data)
        compra_venta = numeroATexto_CompraVenta(form.compra_venta.data)
        con_hipoteca = numeroATexto_Hipoteca(form.con_hipoteca.data)
        opcion_broker = numeroATexto_OpcionBroker(form.opcion_broker.data)
        tipo_pagador = numeroATexto_TipoPagador(form.tipo_pagador.data)
        plazo = form.plazo.data
        cuota_puente = "No"
        if esquema == "CUOTA PUENTE": cuota_puente == "Sí"

        cuota_mixta = form.cuota_mixta.data
        if cuota_mixta != '': cuota_mixta = float(cuota_mixta)

        lista_distritos = lista_distritos
        lista_tipos_propiedades = lista_tipos_propiedades
        lista_niveles_riesgos = lista_niveles_riesgos
        lista_tipos_deudas = lista_tipos_deudas


        
        datos = {
            "nro_operacion": nro_operacion,
            "fecha": obtener_fecha_actual(),
            "dni":dni,
            "tasa_particular" : tasa_particular,
            "comision_particular" : comision_particular,
            "nro_propiedades" : numPropiedades,
            "monto" : form.monto.data,
            "monto_unidad" : numeroATexto_MontoUnidades(form.monto_unidad.data),
            "esquema" : numeroATexto_Esquema(form.esquema.data),
            #"pago_puntual" : numeroATexto_PagoPuntual(form.pago_puntual.data),
            "compra_venta" : numeroATexto_CompraVenta(form.compra_venta.data),
            "con_hipoteca" : numeroATexto_Hipoteca(form.con_hipoteca.data),
            "opcion_broker" : numeroATexto_OpcionBroker(form.opcion_broker.data),
            "tipo_pagador" : numeroATexto_TipoPagador(form.tipo_pagador.data),
            "plazo" : form.plazo.data,
            "cuota_puente": cuota_puente,
            "lista_distritos" : lista_distritos,
            "lista_tipos_propiedades" : lista_tipos_propiedades,
            "lista_niveles_riesgos" : lista_niveles_riesgos,
            "lista_tipos_deudas" : lista_tipos_deudas
        }
        
        with open('datos.json', 'w') as json_file:
            json.dump(datos, json_file, indent=4)
        
        operarComision()
        operarTasa()
        operarCronograma()

        agregar_datos_fondos("cuota_mixta",cuota_mixta)
                    
        agregar_datos("comision_total",extraer_calculo_comision("comision_total"))
        agregar_datos("tasa_final",extraer_calculo_tasa("tasa_final"))
        agregar_datos("nro_operacion",nro_operacion)
        enviardatos()
        nro_operacion = nro_operacion + 1

        return jsonify({'message': 'Los datos de la fueron enviados con éxito.'})

    return render_template('index.html', form=form)

@app.route('/mostrar-cronograma')
def mostrar_cronograma():
    monto = float(extraer_datos("monto"))
    monto_unidad = extraer_datos("monto_unidad")
    plazo = int(extraer_datos("plazo"))
    valor_comision = extraer_calculo_comision("comision_total")
    valor_tasa = extraer_calculo_tasa("tasa_final")
    esquema = extraer_datos("esquema")

    
    lista_fecha_pago, lista_monto_reembolsar, lista_intereses_pactados, lista_amortizacion, lista_cuota_mensual = calcular_cronograma(monto, monto_unidad, plazo, valor_comision, valor_tasa, esquema)
    lista_fecha_pago2, lista_monto_reembolsar2, lista_intereses_pactados2, lista_amortizacion2, lista_cuota_mensual2 = calcular_cronograma2(monto, monto_unidad, plazo, valor_comision, valor_tasa, esquema)
    generar_excel(calcular_cronograma(monto, monto_unidad, plazo, valor_comision, valor_tasa, esquema), "cronograma_p2p.xlsx")
    generar_excel2(calcular_cronograma2(monto, monto_unidad ,plazo, valor_comision, valor_tasa, esquema), "cronograma_fondos.xlsx")
    # Crear un DataFrame con los datos
    data = {
        'Fecha de Pago': lista_fecha_pago,
        'Monto a Reembolsar': lista_monto_reembolsar,
        'Intereses Pactados': lista_intereses_pactados,
        'Amortización': lista_amortizacion,
        'Cuota Mensual': lista_cuota_mensual
    }
    data2 = {
        'Fecha de Pago': lista_fecha_pago2,
        'Monto a Reembolsar': lista_monto_reembolsar2,
        'Intereses Pactados': lista_intereses_pactados2,
        'Amortización': lista_amortizacion2,
        'Cuota Mensual': lista_cuota_mensual2
    }
    df = pd.DataFrame(data)
    df2 = pd.DataFrame(data2)
    # Convertir DataFrame a HTML
    table_html = df.to_html(index=False)
    table_html2 = df2.to_html(index=False)


    monto_solicitado = float(extraer_datos("monto"))
    plazo = extraer_datos("plazo")

    # CRONOGRAMA P2P
    tasa_interes_mensual = float(extraer_datos("tasa_final"))
    ganancia_total = sum(extraer_datos("lista_intereses_pactados"))
    total_reembolsado = float(extraer_datos("monto"))*(1+extraer_datos("comision_total"))
    tasa_interes_nominal_anual = extraer_datos("tasa_final")*12
    despues_impuestos = 0.95 * ganancia_total

    gastos_operativos_porcentaje = round(extraer_calculo_comision("comision_total"),2)
    gastos_operativos_numero = round(gastos_operativos_porcentaje * monto_solicitado,2)
    monto_total = gastos_operativos_numero + monto_solicitado

    flujo = extraer_datos_fondos("flujo")
    TIR = round(npf.irr(flujo),4)
    tea = round((tasa_interes_mensual + 1 )**12-1,4)
    tcea = round((TIR +1)**12 -1,4)


    # CRONOGRAMA DE FONDOS
    tasa_interes_mensual2 = float(extraer_datos_fondos("x"))
    ganancia_total2 = sum(extraer_datos_fondos("lista_intereses_pactados"))
    total_reembolsado2 = float(extraer_datos("monto"))*(1+float(extraer_datos("comision_total")))
    tasa_interes_nominal_anual2 = float(extraer_datos_fondos("x"))*12
    despues_impuestos2 = 0.95 * ganancia_total

    gastos_operativos_porcentaje2 = round(extraer_datos_fondos("gastos_operativos_porcentaje"),2)
    gastos_operativos_numero2 = round(extraer_datos_fondos("gastos_operativos_numero"),2)
    monto_total2 = extraer_datos_fondos("monto_total")

    flujo2 = extraer_datos_fondos("flujo2")
    TIR2 = round(npf.irr(flujo2),4)
    tea2 = round((tasa_interes_mensual2 + 1 )**12-1,4)
    tcea2 = round((TIR2+1)**12 -1,4)
    
    
    

    return render_template('mostrar_cronograma.html', table=table_html, table2=table_html2, 
                            tasa_interes_mensual=tasa_interes_mensual,

                            monto_solicitado=monto_solicitado, 
                            monto_unidad=monto_unidad,
                            plazo=plazo,
                            gastos_operativos_porcentaje=gastos_operativos_porcentaje,
                            gastos_operativos_numero=gastos_operativos_numero,
                            monto_total=monto_total,
                            TIR=TIR, tea=tea, tcea=tcea,
                            
                            gastos_operativos_porcentaje2=gastos_operativos_porcentaje2,
                            gastos_operativos_numero2=gastos_operativos_numero2,
                            monto_total2=monto_total2,
                            tasa_interes_mensual2=tasa_interes_mensual2, 
                            TIR2=TIR2, tea2=tea2, tcea2=tcea2)



@app.route('/descargar-excel')
def descargar_excel():
    return send_file('cronograma_p2p.xlsx')

@app.route('/descargar-excel2')
def descargar_excel2():
    return send_file('cronograma_fondos.xlsx')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

from random import choice, randint
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

def captcha(width=200, height=100):
    # символы для капчи выбираем с таким расчетом,
    # что бы посетители их не спутали с похожими
    # например букву `l` и цифру `1` легко спутать
    # генерация кода капчи из 5 символов
    code = ''.join([choice('QERTYUPLKJHGFDSAZXCVBN23456789') for i in range(5)])
    # сгенерированный код пишем в сессию
    # session['code'] = code

    # создаем подложку
    img = Image.new('RGB', (width,height), (255,255,255))
    # получаем контекст рисования
    draw = ImageDraw.Draw(img)

    # Подключаем растровый шрифт (укажите свой)
    font = ImageFont.truetype('/usr/share/fonts/truetype/freefont/FreeSans.ttf',
                              size=50)
    # начальное положение символов кода
    x=0; y=12;
    # наносим код капчи
    for let in code:
        if x == 0: x = 5
        else: x = x + width/5
        # случайное положение по высоте
        y = randint(3,55)
        # наносим символ
        draw.text((x,y), let, font=font, fill=(randint(0,200), randint(0,200), randint(0,200), 128))

    # создаем шум капчи (в данном случае черточки)
    # можно создать шум точками (кому как нравиться)
    for i in range(40):
        draw.line([(randint(0,width),randint(0,height)),
                   (randint(0,width),randint(0,height))],
                  randint(0, 200), 2, 128)

    # создаем объект в буфере
    f = BytesIO()
    # сохраняем капчу в буфер
    img.save(f, "PNG")
    # возвращаем капчу как байтовый объект
    return  f.getvalue()

# def start():
#     error = False
#     if request.method == "POST":
#         # получаем данные формы
#         input_captcha = request.values.get('input_captcha')
#         # получаем данные сессии
#         sess_captcha = session.get('code')
#         # сравниваем данные сессии и формы
#         if str(input_captcha).lower() == str(sess_captcha).lower():
#             # при успехе перенаправляем на
#             # страничку приветствия
#             return redirect(url_for('hello'))
#         else:
#             # при неправильном вводе кода
#             # капчи - показываем надпись
#             error = True
#     return render_template('capcha.html', error=error)
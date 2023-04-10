function conditionsGenerate(form, input, label) {
  x = input.value;
  var input, label;
  var parent = document.getElementById("parent-conditions");
  cleanDiv(parent)
  for (y = 0; x > y; y++) {
    m_label = document.createElement('label');
    m_label.innerText = 'condition ' + y;
    input_x = document.createElement('input');
    input_x.setAttribute('type', 'str');
    input_x.value = '';
    input_x.setAttribute('name', 'cond_key '+y);
    label_x = document.createElement('label');
    label_x.setAttribute('for', 'cond_key '+y);
    label_x.innerText = 'column name';
    input_y = document.createElement('input');
    input_y.setAttribute('type', 'str');
    input_y.setAttribute('value', '');
    input_y.setAttribute('name', 'cond_val '+y);
    label_y = document.createElement('label');
    label_y.setAttribute('for', 'cond_val '+y);
    label_y.innerText = 'condition: ';
    parent.appendChild(m_label);
    parent.appendChild(label_x);
    parent.appendChild(input_x);
    parent.appendChild(label_y);
    parent.appendChild(input_y);
    parent.appendChild(document.createElement('br'));
  }
}

function cleanDiv(div){
  div.innerHTML = '';
}

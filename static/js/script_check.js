$(document).ready(function () {


  // --------------------------------------------------------
  // запрашиваем список всех правил проверки
  getListRules();

  // --------------------------------------------------------
  // ф-я получает с сервера список правил проверки
  function getListRules() {
    $.ajax({
      // url: "server.php?page=clients&action=fetchData",
      url: "/get-list-rules",
      type: "POST",
      dataType: "json",
      success: function (response) {
        var data = response.data;
        // console.log("список проверок ->");
        // console.log(data);
        $.each(data.list, function (index, value) {
          // console.log(index, value.description);
          // создаем строку списка
          var section_str = value.section.toLowerCase().charAt(0).toUpperCase() + value.section.slice(1).toLowerCase();
          section_str = section_str.replace(/_/g, ' ');
          var contentStr = '<li class="list-group-item"><strong>' + section_str + '</strong> — ' + value.description + '</li>';
          var listItem = $(contentStr);
          // Добавляем созданный элемент в конец списка
          $('#list-rules').append(listItem);

        })
        getUserRules();
      }
    })
  };


  // --------------------------------------------------------
  // ф-я получает с сервера список правил проверки
  function getUserRules() {
    $.ajax({
      url: "/get-user-rulles",
      type: "POST",
      dataType: "json",
      success: function (response) {
        var data = response.data;
        updateShowUserRules(data);
      }
    })
  };

  function updateShowUserRules(listUserRules) {
    $(".user-rules-list").remove();
    $.each(listUserRules, function (index, value) {
      // создаем строку списка
      var section_str = value.section.toLowerCase().charAt(0).toUpperCase() + value.section.slice(1).toLowerCase();
      section_str = section_str.replace(/_/g, ' ');
      var contentStr = '<li class="list-group-item user-rules-list"><strong>' + section_str + '</strong> — ' + value.description +
        '<button type="button" data-id="' + value.rule_id + '" class="btn btn-outline-secondary btn-edit-rule" ><i class="bi bi-pencil"></i></button>' +
        '<button type="button" data-id="' + value.rule_id + '" class="btn btn-outline-secondary btn-del-rule" ><i class="bi bi-trash3"></i></button>' +
        '</li>';
      var listItem = $(contentStr);
      // Добавляем созданный элемент в конец списка
      $('#list-rules').append(listItem);
    })
  };



  // --------------------------------------------------------
  // Ф-я удаляет выбранное правило  
  $("#list-rules").on("click", ".btn-del-rule", function () {
    // получаем data-id из button
    var id = $(this).data('id');

    // console.log('ID:', id);
    $.ajax({

      url: "/del-user-rulle",
      type: "POST",
      dataType: "json",
      data: {
        rule_id: id
      },
      success: function (response) {
        if (response.statusCode == 200) {
          updateShowUserRules(response.data);
          $("#successToast").toast("show");
          $("#successMsg").html(response.message);
        } else if (response.statusCode == 500) {

          $("#errorToast").toast("show");
          $("#errorMsg").html(response.message);
        } else if (response.statusCode == 400) {

          $("#errorToast").toast("show");
          $("#errorMsg").html(response.message);
        }
      }
    })

  });

  // --------------------------------------------------------
  // Ф-я запрашивает с сервера данные по конкретному правилу и 
  // открывает модальное окно для редактирования
  $("#list-rules").on("click", ".btn-edit-rule", function () {
    // получаем data-id из button
    var id = $(this).data('id');

    // console.log('ID:', id);
    $.ajax({

      url: "/get-one-user-rulle",
      type: "POST",
      dataType: "json",
      data: {
        rule_id: id
      },
      success: function (response) {
        if (response.statusCode == 200) {
          // console.log('response', response);
          // подготавливаем модальное окно
          prepareModalBlock();
          // устанавливаем значения модального окна под конкретное правило
          setModalBlock(response.data);
          // устанавливаем значение action как на обновления правила
          $('.modal-body input[name="action"]').val('update');
          // открываем модальное окно
          $('#addRuleModal').modal('show');
          // $("#successToast").toast("show");
          // $("#successMsg").html(response.message);
        } else if (response.statusCode == 500) {

          $("#errorToast").toast("show");
          $("#errorMsg").html(response.message);
        } else if (response.statusCode == 400) {

          $("#errorToast").toast("show");
          $("#errorMsg").html(response.message);
        }
      }
    })

  });

  // --------------------------------------------------------
  //список опций для формирования новых правил проверки
  var var_options;
  getVarsOptions();

  // --------------------------------------------------------
  // ф-я получает с сервера список опций для составления новых правил проверки
  function getVarsOptions() {
    $.ajax({

      url: "/get-vars-options",
      type: "POST",
      dataType: "json",
      success: function (response) {
        // var data = response.data;
        // console.log("список проверок ->");
        // console.log(response);
        var_options = response;

      }
    })
  };

  // --------------------------------------------------------
  // ф-я подготовки модального окна для открытия
  function prepareModalBlock() {

    // очистить select-ы
    $('#select-section').empty();
    $('#select-function').empty();

    // Добавляем нулевую строку селект
    var contentStr = '<option disabled selected value="">Выберите секцию</option>';
    $('#select-section').append($(contentStr));
    // добавляем остальные строки селект
    $.each(var_options.section, function (index, value) {
      var contentStr = '<option value="' + value.id_section + '">' + value.name + '</option>';
      var listItem = $(contentStr);
      // Добавляем созданный элемент в конец списка
      $('#select-section').append(listItem);
    })
    // Добавляем нулевую строку селект
    var contentStr = '<option disabled selected value="">Выберите функцию</option>';
    $('#select-function').append($(contentStr));
    // добавляем остальные строки селект
    $.each(var_options.func_check, function (index, value) {
      var contentStr = '<option value="' + value.id_func + '">' + value.name + '</option>';
      var listItem = $(contentStr);
      // Добавляем созданный элемент в конец списка
      $('#select-function').append(listItem);
    })
    // удаляем поля ввода аргументов функций
    $('.varx').empty();
    // сбрасываем форму
    $('#modalAddForm').trigger('reset');
  }

  // --------------------------------------------------------
  // ф-я установки значений модального окна 
  function setModalBlock(data) {
    // console.log('data', data)
    // console.log("data['description']", data['description'])
    // Прописываем id правила
    $('.modal-body input[name="rule_id"]').val(data['rule_id']);
    // устанавливаем selected  в select-section
    $('#select-section option').filter(function () {
      return $(this).text() === data['section'];
    }).prop('selected', true);

    // устанавливаем selected  в select-function
    $("#select-function").val(data['func']);

    
    // устанавливаем selected  в select-function
    $("#select-importance").val(data['severity']);

    // прописываем значения в текстовые поля
    $('textarea[name="rule_desc"]').val(data['description']);
    $('textarea[name="gost_ref"]').val(data['gost_ref']);

    // Открываем поля для аргументов функций в зависимости от функции и прописываем в них значения
    // создаем и заполняем поял ввода аргументов функций
    $('.varx').empty();
    // console.log("change select");
    var selectedValue = data['func'];

    // console.log(selectedValue); // Выведет значение выбранной
    // const args = getArgsByIdFunc(var_options.func_check, selectedValue);
    const args = data['args'];

    if (args) {
      // console.log(args); // массив аргументов
      $.each(args, function (index, value) {
        var contentStr = '<div class="row justify-content-center py-2">';
        contentStr = contentStr + '<div class="col-sm-12">';
        contentStr = contentStr + '<div class="input-group mb-3">';
        contentStr = contentStr + '<span class="input-group-text">' + value.desc + '</span>';
        contentStr = contentStr + '<input type="text" class="form-control" name="' + value.name + '" value="' + value.val + '">';
        contentStr = contentStr + '<span class="input-group-text">' + value.um + '</span>';
        contentStr = contentStr + '</div></div></div>';
        var listItem = $(contentStr);
        // Добавляем созданный элемент в конец списка
        $('.varx').append(listItem);
      })
    } else {
      console.log('Функция не найдена');
    }
  }

  // --------------------------------------------------------
  // отрабатываем нажатие на кнопку открыть модальное окно
  // чтобы добавить новое правило проверки
  $("#btn-add-rule").on("click", function () {
    // подготовка модального окна
    prepareModalBlock();
    // устанавливаем значение action как на создание нового правила
    $('.modal-body input[name="action"]').val('create');
    // открываем модальное окно
    $('#addRuleModal').modal('show');
  });

  // --------------------------------------------------------
  // ф-я получает из массива var_options по ключу id_func массив аргументов функции
  function getArgsByIdFunc(funcArray, targetId) {
    const found = funcArray.find(item => item.id_func === targetId);
    return found ? found.agr : null; // или []
  }


  // --------------------------------------------------------
  // отрабатываем изменение select в modal-ном окне когда изменяем или выбираем 
  $("#select-function").change(function () {
    // jочищаем предыдущие поля ввода аргументов
    $('.varx').empty();
    // console.log("change select");
    var selectedValue = $(this).val();

    // console.log(selectedValue); // Выведет значение выбранной
    const args = getArgsByIdFunc(var_options.func_check, selectedValue);

    if (args) {
      // console.log(args); // массив аргументов
      $.each(args, function (index, value) {
        var contentStr = '<div class="row justify-content-center py-2">';
        contentStr = contentStr + '<div class="col-sm-12">';
        contentStr = contentStr + '<div class="input-group mb-3">';
        contentStr = contentStr + '<span class="input-group-text">' + value.desc + '</span>';
        contentStr = contentStr + '<input type="text" class="form-control" name="' + value.name + '">';
        contentStr = contentStr + '<span class="input-group-text">' + value.um + '</span>';
        contentStr = contentStr + '</div></div></div>';
        var listItem = $(contentStr);
        // Добавляем созданный элемент в конец списка
        $('.varx').append(listItem);
      })
    } else {
      console.log('Функция не найдена');
    }
  });

  // --------------------------------------------------------
  // ф-я которая отправляет новое созданное правило на север
  $("#modalAddForm").on("submit", function (e) {
    $("#submitBtnModal").attr("disabled", "disabled");
    var action = $('.modal-body input[name="action"]').val();
    var url = "/add-rulle";
    if (action == 'update') {
      url = "/update-user-rulle";
    }
    e.preventDefault();
    $.ajax({
      url: url,
      type: "POST",
      data: new FormData(this),
      contentType: false,
      cache: false,
      processData: false,
      success: function (response) {
        // console.log("response", response);
        // var response = JSON.parse(response);
        // console.log("response", response);
        if (response.statusCode == 200) {
          $('#modalAddForm').trigger('reset');
          // делаем доступной кнопку отправки
          $("#submitBtnModal").removeAttr("disabled");
          // сообщаем что все прошло хорошо
          $("#successToast").toast("show");
          $("#successMsg").html(response.message);
          $('#addRuleModal').modal('hide');
          updateShowUserRules(response.data);
        } else if (response.statusCode == 500) {

          $("#submitBtnModal").removeAttr("disabled");
          $("#errorToast").toast("show");
          $("#errorMsg").html(response.message);
        } else if (response.statusCode == 400) {

          $("#submitBtnModal").removeAttr("disabled");
          $("#errorToast").toast("show");
          $("#errorMsg").html(response.message);
        }
      }
    });
  });

  // --------------------------------------------------------
  // ф-я - инициализации страницы к первоначальному виду
  function initPage() {
    // прячем блок кнопки отправки файла
    $("#blockSend").prop('hidden', true);
    // показываем кнопку из блок кнопки отправки файла
    $("#block-send-btn").prop('hidden', false);
    // прячем секцию на ссылку на скачивание отчета
    $(".block-report-download").prop('hidden', true);

    // очищаем имя файла
    $("#fileName").text(null);
    // очистка содержимого секции
    $(".block-report-success").empty();
    $(".block-report-bad").empty();
    $(".block-report-recomendation").empty();
    $(".block-report-skip").empty();
  };

  // --------------------------------------------------------
  // инициализируем страницу
  initPage();


  // --------------------------------------------------------
  // ф-я которая делает некоторые проверки, 
  // после того как мы на стороне браузера выбрали файл
  $("input.image").change(function () {
    initPage();
    var file = this.files[0];
    var url = URL.createObjectURL(file);

    // Проверка размера файла
    if ($(this)[0].files[0].size > 10 * 1024 * 1024) {
      $("#errorToast").toast("show");
      $("#errorMsg").html('Размер файла превышает 10МБ.');
      return;
    }

    // Проверка на пустой файл
    if ($(this)[0].files[0].size === 0) {
      $("#errorToast").toast("show");
      $("#errorMsg").html('Выбранный файл пустой или поврежден.');
      return;
    }

    // Проверка типа файла
    const fileName = $(this)[0].files[0].name;
    const fileExt = fileName.toLowerCase().split('.').pop();
    if (!['docx'].includes(fileExt)) {
      // if (!['docx', 'pdf'].includes(fileExt)) {
      $("#errorToast").toast("show");
      $("#errorMsg").html('Пожалуйста, загрузите файл в формате DOCX.');
      return;
    }

    // ф-я которая выводит имя файла
    $('#fileName').text($(this)[0].files[0].name);
    // отображаем блок кнопки отправки
    $("#blockSend").prop('hidden', false);

  });

  // --------------------------------------------------------
  // ф-я прописывает ссылку в href тега <a>
  function editLinkReport(nameFile) {
    $('#report_link').attr('href', nameFile);
  };




  // --------------------------------------------------------
  // ф-я которая отправляет файл на проверку на север
  $("#uploadForm").on("submit", function (e) {
    $("#submitBtn").attr("disabled", "disabled");
    e.preventDefault();
    $.ajax({
      url: "/check",
      type: "POST",
      data: new FormData(this),
      contentType: false,
      cache: false,
      processData: false,
      success: function (response) {
        // console.log("response", response);
        // var response = JSON.parse(response);
        // console.log("response", response);
        if (response.statusCode == 200) {
          // прячем блок кнопки отправки файла
          $("#block-send-btn").prop('hidden', true);
          // создаем блок рекомендации
          createRecomendationSectionBlock(response.data.list);
          // создаем блок не пройденных проверок
          createBadSectionBlock(response.data.list);
          // создаем блок пропущенных проверок
          createSkipSectionBlock(response.data.list);
          // создаем блок удачных проверок
          createSuccessSectionBlock(response.data.list);
          // Прописываем ссылку на скачивание <a>
          editLinkReport(response.report_url);
          // Прописываем ссылку на скачивание <button>
          setReportUrl(response.report_url);
          // показываем секцию на скачивание отчета
          $(".block-report-download").prop('hidden', false);
          // делаем доступной кнопку отправки файла
          $("#submitBtn").removeAttr("disabled");
          // сообщаем что все прошло хорошо
          $("#successToast").toast("show");
          $("#successMsg").html(response.message);

        } else if (response.statusCode == 500) {
          // прячем блок кнопки отправки файла
          $("#blockSend").prop('hidden', true);
          $("#submitBtn").removeAttr("disabled");
          $("#errorToast").toast("show");
          $("#errorMsg").html(response.message);
        } else if (response.statusCode == 400) {
          // прячем блок кнопки отправки файла
          $("#blockSend").prop('hidden', true);
          $("#submitBtn").removeAttr("disabled");
          $("#errorToast").toast("show");
          $("#errorMsg").html(response.message);
        }
      }
    });
  });

  // --------------------------------------------------------
  // ф-я генерирует один элемент для блоков "ошибка", "рекомендация" и "пропущенно"
  function getItemBlock(id_parent, flush_n, section_str, desc_str, gost_str, message_str) {
    var section = section_str.toLowerCase().charAt(0).toUpperCase() + section_str.slice(1).toLowerCase();
    section_str = section;
    section_str = section_str.replace(/_/g, ' ');
    var s1 = `<div class="accordion-item rep rule_1">
              <h2 class="accordion-header">
                <button class="accordion-button collapsed " type="button" data-bs-toggle="collapse" data-bs-target="#${flush_n}" aria-expanded="false" aria-controls="${flush_n}">
                <strong> ${section_str} </strong> ` + ` — ` + ` ${desc_str}
                </button>
              </h2>
							<div id="${flush_n}" class="accordion-collapse collapse" data-bs-parent="#${id_parent}">
								<div class="accordion-body">
                  <p>${gost_str}</p> `;
    var s2 = `<hr><p>${message_str}</p>`;
    var s3 = `</div>
							</div>
						</div>`;

    if (message_str == null) {
      return s1 + s3;
    }
    return s1 + s2 + s3;

  };

  // --------------------------------------------------------
  //ф-я возвращает содержимое Section block 
  function getSectionBlock(id_accordion, id_parent, id_collapse, content, icon_name, name_str) {
    return `
      <div class="container">
        <div class="row justify-content-center py-4">
          <div class="col-12">
    
          <div class="accordion" id="${id_accordion}">
            <div class="accordion-item">
              <h2 class="accordion-header">
          
                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#${id_collapse}" aria-controls="${id_collapse}">
                    <div class="fs-3">
                      <i class="bi ${icon_name}" style="font-size: 2rem;"></i>
                      ${name_str}
                    </div>
                </button>
              </h2>
              <div id="${id_collapse}" class="accordion-collapse collapse" data-bs-parent="#${id_accordion}">
                <div class="accordion-body">                
                  <div class="accordion accordion-flush" id="${id_parent}">
                    ${content}
                  </div>
								</div>
							</div>
						</div>							  
					</div>
        </div>
      </div>
		</div>`;
  };

  // --------------------------------------------------------
  // ф-я создает секцию отчета рекомендаций
  function createRecomendationSectionBlock(data) {
    var id_accordion = "accordionReportRecomendation";
    var id_parent = "accordionRecomendation";
    var icon = "bi-exclamation-square text-warning";
    var name_str = "Рекомендации";
    var id_collapse = "collapseReportRecomendation";

    var section_class = ".block-report-recomendation";
    var flagContent = false;
    var contentStr = "";
    var blockStr = "";
    var flush = "flush_recomendation_collapse_";

    $.each(data, function (key, value) {
      if (value.severity == "RECOMMENDATION" && value.status == "FAIL") {
        flagContent = true;
        flush_n = flush + key;
        contentStr = contentStr + getItemBlock(id_parent, flush_n, value.section, value.description, value.gost_ref, value.message);
      }

    });
    // очистка содержимого секции
    $(section_class).empty();

    //если данный контент НЕ было то выходим
    if (flagContent == false) {
      return;
    }

    //создаем строку блока
    blockStr = getSectionBlock(id_accordion, id_parent, id_collapse, contentStr, icon, name_str);

    // переводим строку в код
    var sectionContent = $(blockStr);
    // Добавляем созданный контент внутрь секции
    $(section_class).append(sectionContent);
  };

  // --------------------------------------------------------
  // ф-я создает секцию отчета непройденных проверок
  function createBadSectionBlock(data) {
    var id_accordion = "accordionReportBad";
    var id_parent = "accordionBad";
    var icon = "bi-x-square text-danger";
    var name_str = "Не пройденные правила";
    var id_collapse = "collapseReportBad";

    var section_class = ".block-report-bad";
    var flagContent = false;
    var contentStr = "";
    var blockStr = "";
    var flush = "flush_bad_collapse_";

    $.each(data, function (key, value) {
      if (value.severity == "CRITICAL" && value.status == "FAIL") {
        flagContent = true;
        var flush_n = flush + key;
        contentStr = contentStr + getItemBlock(id_parent, flush_n, value.section, value.description, value.gost_ref, value.message);
      }

    });


    // очистка содержимого секции
    $(section_class).empty();

    //если данный контент НЕ было то выходим
    if (flagContent == false) {
      return;
    }

    //создаем строку блока
    blockStr = getSectionBlock(id_accordion, id_parent, id_collapse, contentStr, icon, name_str);

    // переводим строку в код
    var sectionContent = $(blockStr);
    // Добавляем созданный контент внутрь секции
    $(section_class).append(sectionContent);
  };

  // --------------------------------------------------------
  // ф-я создает секцию отчета пропущенных
  function createSkipSectionBlock(data) {
    var id_accordion = "accordionReportSkip";
    var id_parent = "accordionSkip";
    var icon = "bi-square";
    var name_str = "Пропущенные правила";
    var id_collapse = "collapseReportSkip";

    var section_class = ".block-report-skip";
    var flagContent = false;
    var contentStr = "";
    var blockStr = "";
    var flush = "flush_skip_collapse_";

    $.each(data, function (key, value) {
      if (value.status == "SKIP") {
        flagContent = true;
        var flush_n = flush + key;
        contentStr = contentStr + getItemBlock(id_parent, flush_n, value.section, value.description, value.gost_ref, value.message);
      }

    });

    // очистка содержимого секции
    $(section_class).empty();

    //если данный контент НЕ было то выходим
    if (flagContent == false) {
      return;
    }

    //создаем строку блока
    blockStr = getSectionBlock(id_accordion, id_parent, id_collapse, contentStr, icon, name_str);

    // переводим строку в код
    var sectionContent = $(blockStr);
    // Добавляем созданный контент внутрь секции
    $(section_class).append(sectionContent);
  };

  // --------------------------------------------------------
  // ф-я создает секцию отчета пройденных проверок
  function createSuccessSectionBlock(data) {
    var id_accordion = "accordionReportSuccess";
    var id_parent = "accordionSuccess";
    var icon = "bi-check2-square text-success";
    var name_str = "Успешно пройденные проверки";
    var id_collapse = "collapseReportSuccess";

    var section_class = ".block-report-success";
    var flagContent = false;
    var contentStr = '<ol class="list-group list-group-numbered">';
    var blockStr = "";
    // var flush = "flush_skip_collapse_";

    $.each(data, function (key, value) {
      if (value.status == "OK") {
        flagContent = true;
        var section_str = value.section.toLowerCase().charAt(0).toUpperCase() + value.section.slice(1).toLowerCase();
        section_str = section_str.replace(/_/g, ' ');
        contentStr = contentStr + '<li class="list-group-item"><strong>' + section_str + '</strong> — ' + value.description + '</li>';
      }

    });
    contentStr = contentStr + '</ol>';

    // очистка содержимого секции
    $(section_class).empty();

    //если данный контент НЕ было то выходим
    if (flagContent == false) {
      return;
    }

    //создаем строку блока
    blockStr = getSectionBlock(id_accordion, id_parent, id_collapse, contentStr, icon, name_str);


    // переводим строку в код
    var sectionContent = $(blockStr);
    // Добавляем созданный контент внутрь секции
    $(section_class).append(sectionContent);
  };

  // --------------------------------------------------------
  // Сохраним этот URL в переменную
  let currentReportUrl = null;

  // --------------------------------------------------------
  // ф-я сохраняет URL 
  function setReportUrl(url) {
    currentReportUrl = url;
    // $('#downloadReportBtn').show();
  }


  // --------------------------------------------------------
  // Обрабатываем кнопку скачать отчет
  $('#downloadReportBtn').on('click', function () {
    if (!currentReportUrl) return;

    // Выполняем AJAX-запрос, ожидая бинарные данные (blob)
    $.ajax({
      url: currentReportUrl,
      method: 'GET',
      xhrFields: {
        responseType: 'blob'  // важно: получаем blob
      },
      success: function (data, status, xhr) {
        // Определяем имя файла из заголовка Content-Disposition, если есть
        let disposition = xhr.getResponseHeader('Content-Disposition');
        let filename = 'report.pdf';
        if (disposition && disposition.indexOf('filename=') !== -1) {
          filename = disposition.split('filename=')[1].replace(/["']/g, '');
        }
        // Создаём ссылку для скачивания
        const blob = new Blob([data], { type: 'application/pdf' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
      },
      error: function (xhr, status, error) {
        $("#errorToast").toast("show");
        $("#errorMsg").html("Не удалось скачать отчет или ссылка устарела.");
      }
    });
  });




});
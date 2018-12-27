class_list = []
srcdb = ''

saved_classes = {}

$(document).ready(function(event) {
    $('input[name=srcdb]').val('2191');
    $('#submit_search').click(function(){
        kw = $('input[name=keyword]')[0].value;
        srcdb = $('input[name=srcdb]')[0].value;
        if (kw=='') {
            alert('Search query cannot be blank');
            return;
        }
        $('.search_results .loader').addClass('active')
        $.ajax({
            type:'POST',
            url:'/search',
            data: {
                'type':'keyword',
                'keyword':kw,
                'srcdb':srcdb,
            },
            success: proc_keyword_data
        });

    });

});

function proc_keyword_data(data){
    data = JSON.parse(data)
    if (data.count <= 0){
        alert(data)
    }
    class_list = data.results;
    $('.search_results .ui.cards').empty();
    var i = 0;
    curr_class = class_list[0].code;
    while (i<class_list.length){
        counts = {}
        curr_class = class_list[i].code;
        curr_title = class_list[i].title
        while (i < class_list.length && class_list[i].code==curr_class){
            key = class_list[i].schd
            if (key in counts){
                counts[key] += 1
            } else {
                counts[key] = 1
            }
            i+=1
        }
        //Build card
        card_html = `<div class="card"><div class="content"><div class="header">${curr_class}</div>`;
        card_html += `<div class="description">${class_list[i-1].title}</div>`;
        card_html += `<br/>`
        card_html += '<div class="meta">';
        if ('LEC' in counts){
            card_html += `${counts['LEC']} lectures, `
        }
        if ('REC' in counts){
            card_html += `${counts['REC']} recitations, `
        }
        if ('LAB' in counts){
            card_html += `${counts['LAB']} labratories, `
        }
        if ('SEM' in counts){
            card_html += `${counts['SEM']} seminars, `
        }
        if ('PRA' in counts){
            card_html += `${counts['PRA']} practicums, `
        }
        card_html = card_html.slice(0, -2);
        card_html += `</div></div><div class="ui bottom attached button" onclick="view_sections(${i})">View Sections</div></div>`
        card = $.parseHTML(card_html)
        $('.search_results .ui.cards').append(card)
        $(card).popup({
            html: `<h3>${curr_class} - ${curr_title}</h3><div id="popup_temp" class="ui active text loader">Getting Details...</div>`,
            position: 'right center',
            on: 'click',
            target: '.search_bar',
            setFluidWidth: false,
            onShow: function(){
                $(this).css({'top': '0px', 'max-width':'850px', 'max-height':'100%', 'overflow-y':'scroll', 'overflow-x':'hidden'});
            },
            onVisible: function(){
                $(this).css({'top': '0px', 'max-width':'850px', 'max-height':'100%', 'overflow-y':'scroll', 'overflow-x':'hidden'});
            }
        });
    }
    $('.loader').removeClass('active')
}

function view_sections(i){
    last = i-1
    curr_class = class_list[last].code
    crns = ''
    ind = last
    while (ind>=0 && class_list[ind].code==curr_class){
        crns = ',' + class_list[ind].crn + crns
        ind-=1
    }
    crns = crns.slice(1)
    $.ajax({
        type:'POST',
        url:'/search',
        data: {
            'type':'view_sections',
            'group':`code:${curr_class}`,
            'key':'',
            'matched':`crn:${crns}`,
            'srcdb':srcdb
        },
        success: function(data){
            showDetails(data);
        }
    });
}

function showDetails(data){
    $('.ui.popup').children().remove();
    $('#popup_temp').removeClass('active');
    data = JSON.parse(data)
    popup_html = `<h3>${data.code} - ${data.title}</h3><div id="popup_temp" class="ui active text loader">Getting Details...</div>`;
    popup_html += `<a class="ui black left ribbon label">Last Updated: ${data.last_updated}</a><br/>`
    popup_html += `<strong>Credit Hours:</strong> <span>${data.hours_text}<span><br/>`;
    if (data.seats=="Varies by section")
        popup_html += "<strong>Max Seats:</strong>"
    popup_html += `<span>${data.seats}</span><br/>`
    if (data.restrict_info!="")
        popup_html += `<span class="info_head">Registration Restrictions</span> <p>${data.restrict_info}</p>`
    if (data.clssnotes!="")
        popup_html += `<span class="info_head">Class Notes</span> <p>${data.clssnotes}</p>`
    popup_html += `<span class="info_head">Course Description</span> <p>${data.description}</p>`
    popup_html += `<span class="info_head">Schedule and Location</span> <p>${data.meeting_html}</p>`;
    popup_html += `<span class="info_head">Instructors</span> <p>${data.instructordetail_html}</p>`;
    bad_section_element = $.parseHTML(data.all_sections);
    headers = $($(bad_section_element).children()[0]).children();
    table = '<table class="ui selectable celled table"><thead><tr><th>Saved</th>'
    for (j = 0; j<headers.length; j++){
        table += `<th>${headers[j].innerText}</th>`;
    }
    table += '</tr></thead>'
    rows = $(bad_section_element).children().slice(1)
    for (r = 0; r<rows.length; r++){
        cells = rows[r].children
        id = cells[0].innerText
        id = id.substring(id.indexOf(':')+1).trim()
        row = `<tr onclick="selectCourseRow(this)"><td><div class="ui checkbox"><input type="checkbox" name="${id}" `;
        if (class_saved(id)){
            row += 'checked';
        }
        row += `><label></label></div></td>`
        for (c = 0; c<cells.length; c++){
            txt = cells[c].innerText
            txt = txt.substring(txt.indexOf(':')+1)
            row += `<td>${txt}</td>`;
        }
        row += '</tr>'
        table += row
    }
    table += '</table>'
    popup_html += table
    $('.ui.popup').append(popup_html);
    $('.ui.popup input[type="checkbox"]').click(function(event){
        toggleSaveCourse($(this));
        event.stopPropagation();
    })
    $('#popup_temp').removeClass('active');
}

function class_saved(id){
    keys = Object.keys(saved_classes);
    for (i = 0; i<keys.length; i++){
        if (keys[i]==id.toString()) return true;
    }
    return false;
}

function selectCourseRow(course){
    code = $('.ui.popup h3')[0].innerText.slice(0, 9);
    crn = course[0].name.trim();
    $.ajax({
        type:'POST',
        url:'/search',
        data:{
            'type':'view_sections',
            'group':`code:${code}`,
            'key':`crn:${crn}`,
            'matched':`crn:${crn}`,
            'srcdb':srcdb
        },
        success: function(data){
            showDetails(data);
        }
    })
}

function toggleSaveCourse(course){
    code = $('.ui.popup h3')[0].innerText.slice(0, 9);
    crn = course[0].name.trim();
    if (course[0].checked){
        $.ajax({
            type:'POST',
            url:'/search',
            data:{
                'type':'view_sections',
                'group':`code:${code}`,
                'key':`crn:${crn}`,
                'matched':`crn:${crn}`,
                'srcdb':srcdb
            },
            success: function(data){
                saved_classes[crn] = data;
                updateCourseList()
            }
        });
    } else {
        delete saved_classes[crn];
        updateCourseList()
    }
}

function updateCourseList(){
    dis = $('#save_display');
    dis.children().remove()
    var sorted = [];
    for(var key in saved_classes) {
        sorted[sorted.length] = key;
    }
    sorted.sort();
    for (var s in sorted){
        v = JSON.parse(saved_classes[sorted[s]]);
        code = v.code;
        if (v.hours_text.includes('Lec')){
            code += ' - LEC';
        }
        else if (v.hours_text.includes('Rec')){
            code += ' - REC';
        }
        else if (v.hours_text.includes('Lab')){
            code += ' - LAB';
        }
        else if (v.hours_text.includes('Sem')){
            code += ' - SEM';
        }
        else if (v.hours_text.includes('Pra')){
            code += ' - PRA';
        }
        ele = $(v.meeting_html)[0]
        ele = ele.innerText
        time = ele.substring(0, ele.indexOf(' in'));
        html = `<div class="item"><div class="right floated content"><div class="ui mini button" style="padding:10px;">
            Toggle</div></div><div id="course_item" class="ui label" style="padding:1px;padding-top:10px;">${code}
            <div class="detail">${time}</div></div></div>`;
        dis.append(html);
    }
}

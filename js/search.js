class_list = []
srcdb = ''

$(document).ready(function(event) {
    $('input[name=srcdb]').val('2191');
    $('#submit_search').click(function(){
        kw = $('input[name=keyword]')[0].value;
        srcdb = $('input[name=srcdb]')[0].value;
        if (kw=='') {
            alert('Search query cannot be blank');
            return;
        }
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
    }
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
            console.log(data)
        }
    });
}

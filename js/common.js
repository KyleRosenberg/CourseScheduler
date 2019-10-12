function loadSections(showAll=true){
    $('#save_display .loader').addClass('active');
    firebase.auth().currentUser.getIdToken(true).then(function(idToken) {
        $.ajax({
            type: 'POST',
            url: '/loadsect',
            data: {
                'uid':firebase.auth().currentUser.uid,
                'token':idToken
            },
            success: function(data){
                saved_classes = {}
                if (data.length==0){
                    saved_classes = {...calendar_classes};
                } else {
                    for (let i = 0; i<data.length; i++){
                        let d = data[i];
                        saved_classes[d['crn']] = JSON.stringify(d)
                    }
                }
                updateCourseList(showAll);
            },
            error: function(xhr, st, er){
                $('#save_display .loader').removeClass('active')
                showError('There was an error loading your saved sections.');
            },
            always: function(){
                console.log('HERE')
                $('.bpcalendar tr td').css('padding', "0px");
            }
        });
    }).catch(function(error) {
        $('#save_display .loader').removeClass('active')
        showError(error);
    });
}

function updateCourseList(showAll=true) {
    dis = $('#save_display');
    dis.children().remove()
    dis.append('<div class="ui text loader">Loading saved sections...</div>');
    var sorted = [];
    for (var key in saved_classes) {
        sorted[sorted.length] = key;
    }
    sorted.sort();
    for (var s in sorted) {
        v = JSON.parse(saved_classes[sorted[s]]);
        if (!showAll){
            if (v.crn.length>5) continue;
        }
        code = buildCourseName(v)
        time = buildCourseTime(v);
        item = '<div class="item" style="padding:3px;">';
        if (showAll){
            item += `<div class="right floated content"><div name="${v.crn}" class="ui mini toggle button" style="padding:10px;" onclick="toggleShowCourse(this)">
                Toggle</div></div>`;
        }
        item += `<div id="course_item" class="ui label" style="padding:1px;padding-top:10px;">${code}
            <div class="detail">${time}</div></div></div>`;
        html = $(item);
        dis.append(html);
        if (showAll && v.crn in calendar_classes) {
            $(html).css('background-color', '#C5C5C5')
        } else { //TODO fiv color stuff ^ v
            $(html).css('background-color', 'transparent')
        }
    }
}

function buildCourseName(v){
    code = v.code;
    if (v.hours_text.includes('Lec')) {
        code += ' - LEC';
    } else if (v.hours_text.includes('Rec')) {
        code += ' - REC';
    } else if (v.hours_text.includes('Lab')) {
        code += ' - LAB';
    } else if (v.hours_text.includes('Sem')) {
        code += ' - SEM';
    } else if (v.hours_text.includes('Pra')) {
        code += ' - PRA';
    }
    return code;
}

function buildCourseTime(v){
    ele = $(v.meeting_html)[0]
    ele = ele.innerText
    time = ele.substring(0, ele.indexOf(' in'));
    return time;
}

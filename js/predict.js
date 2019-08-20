old_class_list = []
recent_results = []

$(document).ready(function(event) {
    firebase.auth().onAuthStateChanged(function(user) {
        if (user) {
            loadSections(false);
            loadCourses();
        }
    });
    $('.ccan').click(function(){
        $('.add input').val('');
        $('.modal.add .checkbox').checkbox('uncheck');
        $('.ui.modal.add').modal('hide');
        $('#predict_results').empty();
    });
    $('.csav').click(function(){
        searchFCQ();
    });
    $('#save_button').click(saveCourses);
});

function showAdd(crn=null){
    curr_edit = crn;
    $('.ui.modal.add').modal({
        closable: false
    }).modal('show');
    $('#year_calendar').calendar({
        type: 'year'
    });
    if (crn!=null){
        //TODO: Implement edit?
    }
}

function addPossibilitiesToSearchModal(data){
    if (!(data instanceof Array)){
        if ('failure' in data)
            showError(data.failure);
        else
            showError("But I don't know what. Sorry.");
        return;
    }
    if (data.length<1){
        showError("No results. Please make sure no fields are blank.")
        return;
    }
    $('#predict_results').empty();
    recent_results = data;
    table = `<table class="ui selectable celled table">
        <thead><tr><th>Course</th><th>Term</th><th>Instructor</th></tr></thead>`;
    for (let i = 0; i<data.length; i++){
        data[i]['Grade'] = $('#grade').val();
        table += `<tr onclick=addOldCourse(${i})>`;
        table += `<td>${data[i].Subject} ${data[i].Course}</td>`;
        table += `<td>${data[i].Term} ${data[i].Year}</td>`;
        table += `<td>${data[i].Instructor_Name}</td>`;
        table += '</tr>';
    }
    table += '</table>';
    $('#predict_results').append(table);
}

function searchFCQ(){
    subject = $('#subject').val();
    course = $('#course').val();
    term = $('#term').val();
    year = $('#year_calendar input').val()
    if (!subject || !course || !term || !year){
        showError("All fields must be filled.");
        return;
    }
    $.ajax({
        type: 'POST',
        url: '/predictsearch',
        data: {
            'term': term,
            'year': year,
            'subject': subject,
            'course': course
        },
        success: function(data) {
            addPossibilitiesToSearchModal(JSON.parse(data));
        }
    });
}

function addOldCourse(index){
    old_class_list.push(recent_results[index]);
    $('.add input').val('');
    $('.modal.add .checkbox').checkbox('uncheck');
    $('.ui.modal.add').modal('hide');
    $('#predict_results').empty();
    updateOldCourseList();
}

function updateOldCourseList(){
    dis = $('#old_display');
    dis.children().remove()
    dis.append('<div class="ui text loader">Loading saved sections...</div>');
    var sorted = [];
    for (var key in old_class_list) {
        sorted[sorted.length] = key;
    }
    sorted.sort();
    for (var k in sorted) {
        s = old_class_list[sorted[k]]
        html = $(`<div class="item" style="padding:3px;"><div id="course_item" class="ui label" style="padding:1px;padding-top:10px;">${s.Subject} ${s.Course}
            <div class="detail">${s.Term} ${s.Year}</div><div class="detail">${s.Grade}</div></div></div>`);
        dis.append(html);
        $(html).css('background-color', 'transparent')
    }
}

function saveCourses(){
    if (!firebase.auth().currentUser){
        $('.ui.modal.google').modal('show');
        return;
    }
    saved = []
    for (var k in old_class_list){
        sc = old_class_list[k]
        s = {}
        s['term'] = sc.Term
        s['year'] = sc.Year
        s['subject'] = sc.Subject
        s['course'] = sc.Course
        s['section'] = sc.Section
        s['instructor'] = sc.Instructor_Name
        s['grade'] = sc.Grade
        saved.push(s)
    }
    firebase.auth().currentUser.getIdToken(true).then(function(idToken) {
        console.log(saved);
        $.ajax({
            type: 'POST',
            url: '/predictsave',
            data: {
                'uid':firebase.auth().currentUser.uid,
                'token':idToken,
                'saved':JSON.stringify(saved)
            },
            success: function(data){
                if (data!='Success'){
                    showError('I don\'t know how you managed this, but this should literally never happen.');
                }
            },
            error: function(xhr, st, er){
                showError('There was an error saving your sections.');
            }
        });
    }).catch(function(error) {
        showError(error);
    });
}

function loadCourses(){
    $('#old_display .loader').addClass('active');
    firebase.auth().currentUser.getIdToken(true).then(function(idToken) {
        $.ajax({
            type: 'POST',
            url: '/predictload',
            data: {
                'uid':firebase.auth().currentUser.uid,
                'token':idToken
            },
            success: function(data){
                old_class_list = []
                for (k in data){
                    old_class_list.push(data[k]);
                }
                updateOldCourseList();
            },
            error: function(xhr, st, er){
                $('#old_display .loader').removeClass('active')
                showError('There was an error loading your saved sections.');
            }
        });
    }).catch(function(error) {
        $('#old_display .loader').removeClass('active')
        showError(error);
    });
}

function tempPredict(){
    firebase.auth().currentUser.getIdToken(true).then(function(idToken) {
        $.ajax({
            type: 'POST',
            url: '/predict',
            data: {
                'uid':firebase.auth().currentUser.uid,
                'token':idToken
            },
            success: function(data){
                console.log(data);
                data = JSON.parse(data);

                for (let i = 0; i<data.length; i++){
                    $('.main_view').append(`<br/><img src="data:image/png;base64, ${data[i].prediction}" alt="Something went wrong lol"/>`);
                }
            },
            error: function(xhr, st, er){
                showError('There was an error loading your saved sections.');
            }
        });
    }).catch(function(error) {
        showError(error);
    });
}

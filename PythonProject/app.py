from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

import os
app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'football_secret_key_123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///football.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Models
class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    logo = db.Column(db.String(200), nullable=True)
    stadium = db.Column(db.String(100), nullable=True)
    coach = db.Column(db.String(100), nullable=True)
    founded_year = db.Column(db.Integer, nullable=True)
    country = db.Column(db.String(50), nullable=True)
    team_color = db.Column(db.String(20), nullable=True)
    players = db.relationship('Player', backref='team', lazy=True)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    position = db.Column(db.String(50), nullable=True)
    number = db.Column(db.Integer, nullable=True)
    age = db.Column(db.Integer, nullable=True)

class Tournament(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='active')  # active, completed
    matches = db.relationship('Match', backref='tournament', lazy=True)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team1_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    team2_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    team1_score = db.Column(db.Integer, nullable=True)
    team2_score = db.Column(db.Integer, nullable=True)
    round_name = db.Column(db.String(50), nullable=False)  # VÒNG 1/16, VÒNG 1/8, TỨ KẾT, BÁN KẾT, CHUNG KẾT
    match_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, completed
    bracket_position = db.Column(db.String(50), nullable=True)  # For bracket positioning
    description = db.Column(db.Text, nullable=True)  # Match description/comments
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournament.id'), nullable=True)

    team1 = db.relationship('Team', foreign_keys=[team1_id])
    team2 = db.relationship('Team', foreign_keys=[team2_id])

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/teams')
def teams():
    search = request.args.get('search', '')
    if search:
        teams = Team.query.filter(Team.name.ilike(f'%{search}%')).all()
    else:
        teams = Team.query.all()
    return render_template('teams.html', teams=teams, search=search)

@app.route('/add_team', methods=['GET', 'POST'])
def add_team():
    if request.method == 'POST':
        name = request.form.get('name')
        logo = request.form.get('logo')
        stadium = request.form.get('stadium')
        coach = request.form.get('coach')
        founded_year = int(request.form.get('founded_year')) if request.form.get('founded_year') else None
        country = request.form.get('country')
        team_color = request.form.get('team_color')
        new_team = Team(
            name=name, 
            logo=logo,
            stadium=stadium,
            coach=coach,
            founded_year=founded_year,
            country=country,
            team_color=team_color
        )
        db.session.add(new_team)
        db.session.commit()
        return redirect(url_for('teams'))
    return render_template('add_team.html')

@app.route('/delete_team/<int:team_id>', methods=['POST'])
def delete_team(team_id):
    team = Team.query.get_or_404(team_id)
    db.session.delete(team)
    db.session.commit()
    return redirect(url_for('teams'))

@app.route('/edit_team/<int:team_id>', methods=['GET', 'POST'])
def edit_team(team_id):
    team = Team.query.get_or_404(team_id)
    if request.method == 'POST':
        team.name = request.form.get('name')
        team.logo = request.form.get('logo')
        team.stadium = request.form.get('stadium')
        team.coach = request.form.get('coach')
        team.founded_year = int(request.form.get('founded_year')) if request.form.get('founded_year') else None
        team.country = request.form.get('country')
        team.team_color = request.form.get('team_color')
        db.session.commit()
        return redirect(url_for('teams'))
    return render_template('edit_team.html', team=team)

@app.route('/team/<int:team_id>/players')
def team_players(team_id):
    team = Team.query.get_or_404(team_id)
    players = Player.query.filter_by(team_id=team_id).all()
    return render_template('team_players.html', team=team, players=players)

@app.route('/team/<int:team_id>/add_player', methods=['GET', 'POST'])
def add_player(team_id):
    team = Team.query.get_or_404(team_id)
    if request.method == 'POST':
        player = Player(
            name=request.form.get('name'),
            team_id=team_id,
            position=request.form.get('position'),
            number=int(request.form.get('number')) if request.form.get('number') else None,
            age=int(request.form.get('age')) if request.form.get('age') else None
        )
        db.session.add(player)
        db.session.commit()
        return redirect(url_for('team_players', team_id=team_id))
    return render_template('add_player.html', team=team)

@app.route('/delete_player/<int:player_id>', methods=['POST'])
def delete_player(player_id):
    player = Player.query.get_or_404(player_id)
    team_id = player.team_id
    db.session.delete(player)
    db.session.commit()
    return redirect(url_for('team_players', team_id=team_id))

@app.route('/bracket')
def bracket():
    matches = Match.query.all()
    teams = Team.query.all()
    return render_template('bracket.html', matches=matches, teams=teams)

@app.route('/schedule_match', methods=['GET', 'POST'])
def schedule_match():
    if request.method == 'POST':
        team1_id = request.form.get('team1_id')
        team2_id = request.form.get('team2_id')
        round_name = request.form.get('round_name')
        match_time = request.form.get('match_time')
        bracket_position = request.form.get('bracket_position')
        description = request.form.get('description')
        
        if team1_id == team2_id:
            flash('Không thể chọn cùng một đội!', 'error')
            teams = Team.query.all()
            return render_template('schedule_match.html', teams=teams)
        
        new_match = Match(
            team1_id=int(team1_id),
            team2_id=int(team2_id),
            round_name=round_name,
            match_time=datetime.strptime(match_time, '%Y-%m-%dT%H:%M') if match_time else None,
            bracket_position=bracket_position,
            description=description
        )
        db.session.add(new_match)
        db.session.commit()
        return redirect(url_for('bracket'))
    
    teams = Team.query.all()
    return render_template('schedule_match.html', teams=teams)

@app.route('/delete_match/<int:match_id>', methods=['POST'])
def delete_match(match_id):
    match = Match.query.get_or_404(match_id)
    db.session.delete(match)
    db.session.commit()
    return redirect(url_for('bracket'))

@app.route('/update_result/<int:match_id>', methods=['GET', 'POST'])
def update_result(match_id):
    match = Match.query.get_or_404(match_id)
    if request.method == 'POST':
        team1_score = request.form.get('team1_score')
        team2_score = request.form.get('team2_score')
        match.team1_score = int(team1_score) if team1_score else 0
        match.team2_score = int(team2_score) if team2_score else 0
        match.status = 'completed'
        db.session.commit()
        return redirect(url_for('bracket'))
    return render_template('update_result.html', match=match)

@app.route('/leaderboard')
def leaderboard():
    teams = Team.query.all()
    standings = []
    
    for team in teams:
        wins = 0
        draws = 0
        losses = 0
        goals_for = 0
        goals_against = 0
        
        # Calculate statistics from completed matches
        team1_matches = Match.query.filter_by(team1_id=team.id, status='completed').all()
        team2_matches = Match.query.filter_by(team2_id=team.id, status='completed').all()
        
        for match in team1_matches:
            score1 = match.team1_score or 0
            score2 = match.team2_score or 0
            goals_for += score1
            goals_against += score2
            if score1 > score2:
                wins += 1
            elif score1 == score2:
                draws += 1
            else:
                losses += 1
        
        for match in team2_matches:
            score1 = match.team1_score or 0
            score2 = match.team2_score or 0
            goals_for += score2
            goals_against += score1
            if score2 > score1:
                wins += 1
            elif score2 == score1:
                draws += 1
            else:
                losses += 1
        
        points = wins * 3 + draws * 1
        goal_difference = goals_for - goals_against
        
        standings.append({
            'team': team,
            'played': wins + draws + losses,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'goals_for': goals_for,
            'goals_against': goals_against,
            'goal_difference': goal_difference,
            'points': points
        })
    
    # Sort by points, then goal difference
    standings.sort(key=lambda x: (-x['points'], -x['goal_difference']))
    
    return render_template('leaderboard.html', standings=standings)

@app.route('/match_history')
def match_history():
    matches = Match.query.order_by(Match.match_time.desc()).all()
    return render_template('match_history.html', matches=matches)

@app.route('/statistics')
def statistics():
    teams = Team.query.all()
    matches = Match.query.filter_by(status='completed').all()
    
    total_matches = len(matches)
    total_goals = sum((m.team1_score or 0) + (m.team2_score or 0) for m in matches)
    total_teams = len(teams)
    
    return render_template('statistics.html', 
                         total_matches=total_matches,
                         total_goals=total_goals,
                         total_teams=total_teams,
                         teams=teams)

@app.route('/reset_data', methods=['POST'])
def reset_data():
    db.session.query(Player).delete()
    db.session.query(Match).delete()
    db.session.query(Team).delete()
    db.session.query(Tournament).delete()
    db.session.commit()
    flash('Đã reset toàn bộ dữ liệu!', 'success')
    return redirect(url_for('index'))

@app.route('/tournaments')
def tournaments():
    tournaments = Tournament.query.all()
    return render_template('tournaments.html', tournaments=tournaments)

@app.route('/add_tournament', methods=['GET', 'POST'])
def add_tournament():
    if request.method == 'POST':
        from datetime import date
        name = request.form.get('name')
        description = request.form.get('description')
        start_date = date.fromisoformat(request.form.get('start_date')) if request.form.get('start_date') else None
        end_date = date.fromisoformat(request.form.get('end_date')) if request.form.get('end_date') else None
        
        new_tournament = Tournament(
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date
        )
        db.session.add(new_tournament)
        db.session.commit()
        return redirect(url_for('tournaments'))
    return render_template('add_tournament.html')

@app.route('/delete_tournament/<int:tournament_id>', methods=['POST'])
def delete_tournament(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    db.session.delete(tournament)
    db.session.commit()
    return redirect(url_for('tournaments'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)

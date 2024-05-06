use serde::{Deserialize, Serialize};
use serde_json;
use std::fs::OpenOptions;
use std::io::{Write, Read};
use std::collections::HashMap;

use crate::goal::Goal;
use crate::project::Project;
use crate::traits::{ObjectId, Id};

#[derive(Deserialize, Serialize)]
pub struct Doit {
    pub goals: HashMap<ObjectId, Goal>,
    pub cur_goal: ObjectId,
    pub cur_project: ObjectId,
    pub path: String,
}


impl Default for Doit {
    fn default() -> Self {
        Doit{
            goals: HashMap::new(),
            cur_goal: "".to_string(),
            cur_project: "".to_string(),
            path: "./.doit.json".to_string()
        }
    }
}

impl Doit {
  
    // Dump contents to JSON file
    pub fn update(&self) {
        
        let mut file = OpenOptions::new()
            .truncate(true)
            .create(true)
            .write(true)
            .open(&self.path)
            .unwrap();
        
        file.write_all(
            serde_json::to_string_pretty(
                &self
            ).unwrap().as_bytes()
        ).unwrap()
    }

    pub fn from_file() -> Self {
        let mut file = OpenOptions::new()
            .read(true)
            .open(Doit::default().path)
            .unwrap(); //proper error handling plz
        
        let mut buf = String::new();
        file.read_to_string(&mut buf).unwrap();
        serde_json::from_str(&buf).unwrap()
    }

    pub fn init() {
        Doit::default().update();
    }

    pub fn create_goal(&mut self, desc: &str) {
        let goal = Goal::new(desc); 
        
        self.goals.insert(
            goal.id(),
            goal
        );

        self.update();
    }

    pub fn create_project(
            &mut self, 
            ghub_url: &str
        ) {

        let project = Project::new(ghub_url);

        self.goals.get_mut(&self.cur_goal)
            .expect("No goal selected") //replace with actual error
            .projects
            .insert(
                project.id(), 
                project
            );
        
        self.update();
    }

    pub fn select(&mut self, object_id: &ObjectId) {
        //Try to find hash in goals
        if self.goals.contains_key(object_id) {
            self.cur_goal = object_id.to_string();
        }

        //Try to find hash in any project
        for goal in &self.goals {
            if goal.1.projects.contains_key(object_id) {
                self.cur_project = object_id.to_string();
                return;
            }
        }

        eprintln!("no object with id {} could be found", object_id);
    }

    pub fn list_goals(&self) {
        let _: Vec<_> = self.goals.values().map(|goal| {
            println!("{}", goal);
        }).collect();

    }

    pub fn list_projects(&self, object_id: Option<&ObjectId>) {
        let target = object_id.unwrap_or(&self.cur_project);

        let _: Vec<_> = self.goals.get(target)
            .unwrap().projects
            .iter()
            .map(|project|{
                println!("{}", project.1)
            }
        ).collect();

    }
}

